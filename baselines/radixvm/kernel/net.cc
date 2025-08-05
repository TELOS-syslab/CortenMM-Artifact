#include "types.h"
#include "kernel.hh"
#include "queue.h"
#include "spinlock.h"
#include "condvar.h"
#include "proc.hh"
#include "fs.h"
#include "file.hh"
#include "net.hh"
#include "major.h"
#include "netdev.hh"

#ifdef LWIP
extern "C" {
#include "lwip/tcp_impl.h"
#include "lwip/tcpip.h"
#include "lwip/ip.h"
#include "lwip/netif.h"
#include "lwip/dhcp.h"
#include "lwip/sockets.h"
#include "netif/etharp.h"
}

err_t if_init(struct netif *netif);
void if_input(struct netif *netif, void *buf, u16 len);
#endif

netdev *the_netdev;

void
netfree(void *va)
{
  kfree(va);
}

void *
netalloc(void)
{
  return kalloc("(netalloc)");
}

int
nettx(void *va, u16 len)
{
  if (!the_netdev)
    return -1;
  return the_netdev->transmit(va, len);
}

void
nethwaddr(u8 *hwaddr)
{
  if (!the_netdev)
    return;
  the_netdev->get_hwaddr(hwaddr);
}

#ifdef LWIP

static struct netif nif;

struct timer_thread {
  u64 nsec;
  struct condvar waitcv;
  struct spinlock waitlk;
  void (*func)(void);
};

int errno;

void
netrx(void *va, u16 len)
{
  lwip_core_lock();
  if_input(&nif, va, len);
  lwip_core_unlock();
}

static void __attribute__((noreturn))
net_timer(void *x)
{
  struct timer_thread *t = (struct timer_thread *) x;

  for (;;) {
    u64 cur = nsectime();
    
    lwip_core_lock();
    t->func();
    lwip_core_unlock();
    acquire(&t->waitlk);
    t->waitcv.sleep_to(&t->waitlk, cur + t->nsec);
    release(&t->waitlk);
  }
}

static void
start_timer(struct timer_thread *t, void (*func)(void),
            const char *name, u64 msec)
{
  struct proc *p;

  t->nsec = 1000000000 / 1000*msec;
  t->func = func;
  t->waitcv = condvar(name);
  t->waitlk = spinlock(name, LOCKSTAT_NET);
  p = threadalloc(net_timer, t);
  if (p == nullptr)
    panic("net: start_timer");

  acquire(&p->lock);
  safestrcpy(p->name, name, sizeof(p->name));
  addrun(p);
  release(&p->lock);
}

static void
lwip_init(struct netif *xnif, void *if_state,
	  u32 init_addr, u32 init_mask, u32 init_gw)
{
  struct ip_addr ipaddr, netmask, gateway;
  ipaddr.addr  = init_addr;
  netmask.addr = init_mask;
  gateway.addr = init_gw;
  
  if (0 == netif_add(xnif, &ipaddr, &netmask, &gateway,
                     if_state,
                     if_init,
                     ip_input))
    panic("lwip_init: error in netif_add\n");
  
  netif_set_default(xnif);
  netif_set_up(xnif);
}

static void
tcpip_init_done(void *arg)
{
  volatile long *tcpip_done = (volatile long*) arg;
  *tcpip_done = 1;
}

static int
netifread(mdev*, char *dst, u32 off, u32 n)
{
  u32 ip, nm, gw;
  char buf[512];
  u32 len;

  ip = ntohl(nif.ip_addr.addr);
  nm = ntohl(nif.netmask.addr);
  gw = ntohl(nif.gw.addr);

#define IP(x)              \
  (x & 0xff000000) >> 24, \
  (x & 0x00ff0000) >> 16, \
  (x & 0x0000ff00) >> 8,  \
  (x & 0x000000ff)

  snprintf(buf, sizeof(buf),
           "hw %02x:%02x:%02x:%02x:%02x:%02x\n"
           "ip %u.%u.%u.%u nm %u.%u.%u.%u gw %u.%u.%u.%u\n",
           nif.hwaddr[0], nif.hwaddr[1], nif.hwaddr[2],
           nif.hwaddr[3], nif.hwaddr[4], nif.hwaddr[5],
           IP(ip), IP(nm), IP(gw));

#undef IP

  len = strlen(buf);

  if (off >= len)
    return 0;

  n = MIN(len - off, n);
  memmove(dst, &buf[off], n);
  return n;
}

static void
initnet_worker(void *x)
{
  static struct timer_thread t_arp, t_tcpf, t_tcps, t_dhcpf, t_dhcpc;
  volatile long tcpip_done = 0;

  lwip_core_init();

  lwip_core_lock();
  tcpip_init(&tcpip_init_done, (void*)&tcpip_done);
  lwip_core_unlock();
  while (!tcpip_done)
    yield();

  lwip_core_lock();
  memset(&nif, 0, sizeof(nif));
  lwip_init(&nif, nullptr, 0, 0, 0);

  dhcp_start(&nif);

  start_timer(&t_arp, &etharp_tmr, "arp_timer", ARP_TMR_INTERVAL);
  start_timer(&t_tcpf, &tcp_fasttmr, "tcp_f_timer", TCP_FAST_INTERVAL);
  start_timer(&t_tcps, &tcp_slowtmr, "tcp_s_timer", TCP_SLOW_INTERVAL);

  start_timer(&t_dhcpf, &dhcp_fine_tmr,	"dhcp_f_timer",	DHCP_FINE_TIMER_MSECS);
  start_timer(&t_dhcpc, &dhcp_coarse_tmr, "dhcp_c_timer", DHCP_COARSE_TIMER_MSECS);

#if 1
  lwip_core_unlock();
#else
  // This DHCP code is useful for debugging, but isn't necessary
  // for the lwIP DHCP client.
  struct spinlock lk("dhcp sleep");
  struct condvar cv("dhcp cv sleep");
  int dhcp_state = 0;
  const char *dhcp_states[] = {
    [DHCP_RENEWING]  = "renewing",
    [DHCP_SELECTING] = "selecting",
    [DHCP_CHECKING]  = "checking",
    [DHCP_BOUND]     = "bound",
  };

  for (;;) {
    if (dhcp_state != nif.dhcp->state) {
      dhcp_state = nif.dhcp->state;
      cprintf("net: DHCP state %d (%s)\n", dhcp_state,
              dhcp_states[dhcp_state] ? : "unknown");

      if (dhcp_state == DHCP_BOUND) {
        u32 ip = ntohl(nif.ip_addr.addr);
        cprintf("net: %02x:%02x:%02x:%02x:%02x:%02x" 
                " bound to %u.%u.%u.%u\n", 
                nif.hwaddr[0], nif.hwaddr[1], nif.hwaddr[2],
                nif.hwaddr[3], nif.hwaddr[4], nif.hwaddr[5],
                (ip & 0xff000000) >> 24,
                (ip & 0x00ff0000) >> 16,
                (ip & 0x0000ff00) >> 8,
                (ip & 0x000000ff));
      }
    }

    lwip_core_unlock();    
    acquire(&lk);
    cv.sleepto(&lk, nsectime() + 1000000000);
    release(&lk);
    lwip_core_lock();
  }
#endif
}

void
initnet(void)
{
  struct proc *t;

  devsw[MAJ_NETIF].read = netifread;

  t = threadalloc(initnet_worker, nullptr);
  if (t == nullptr)
    panic("initnet: threadalloc");

  acquire(&t->lock);
  safestrcpy(t->name, "initnet", sizeof(t->name));
  addrun(t);
  release(&t->lock);
}

long
netsocket(int domain, int type, int protocol)
{
  int r;
  lwip_core_lock();
  r = lwip_socket(domain, type, protocol);
  lwip_core_unlock();
  return r;
}

long
netbind(int sock, const sockaddr* xaddr, int xaddrlen)
{
  struct sockaddr* addr;
  long r;
  
  addr = (sockaddr*) kmalloc(xaddrlen, "sockaddr");
  if (addr == nullptr)
    return -1;

  if (fetchmem(addr, xaddr, xaddrlen))
    return -1;

  lwip_core_lock();
  r = lwip_bind(sock, addr, xaddrlen);
  lwip_core_unlock();
  kmfree(addr, xaddrlen);
  return r;
}

long
netlisten(int sock, int backlog)
{
  int r;
  
  lwip_core_lock();
  r = lwip_listen(sock, backlog);
  lwip_core_unlock();
  return r;
}

long
netaccept(int sock, struct sockaddr* xaddr, u32* xaddrlen)
{
  socklen_t len;
  void *addr;
  int ss;

  if (fetchmem(&len, xaddrlen, sizeof(*xaddrlen)))
    return -1;

  addr = kmalloc(len, "sockaddr");
  if (addr == nullptr)
    return -1;

  lwip_core_lock();
  ss = lwip_accept(sock, (sockaddr*) addr, &len);
  lwip_core_unlock();
  if (ss < 0) {
    kmfree(addr, len);
    return ss;
  }

  if (putmem(xaddrlen, &len, sizeof(len)) || putmem(xaddr, addr, len)) {
    lwip_core_lock();
    lwip_close(ss);
    lwip_core_unlock();
    kmfree(addr, len);
    return -1;
  }

  return ss;
}

void
netclose(int sock)
{
  lwip_core_lock();
  lwip_close(sock);
  lwip_core_unlock();
}

int
netwrite(int sock, const char *buf, int len)
{
  int r;

  lwip_core_lock();
  r = lwip_write(sock, buf, len);
  lwip_core_unlock();
  return r;
}

int
netread(int sock, char *buf, int len)
{
  int r;

  lwip_core_lock();
  r = lwip_read(sock, buf, len);
  lwip_core_unlock();
  return r;
}

#else

void
initnet(void)
{
}

void
netrx(void *va, u16 len)
{
  netfree(va);
}

long
netsocket(int domain, int type, int protocol)
{
  return -1;
}

long
netbind(int sock, const struct sockaddr *xaddr, int xaddrlen)
{
  return -1;
}

long
netlisten(int sock, int backlog)
{
  return -1;
}

long
netaccept(int sock, struct sockaddr* xaddr, u32* xaddrlen)
{
  return -1;
}

void
netclose(int sock)
{
}

int
netwrite(int sock, const char *buf, int len)
{
  return -1;
}

int
netread(int sock, char *buf, int len)
{
  return -1;
}
#endif
