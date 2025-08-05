#include "types.h"
#include "kernel.hh"
#include "mmu.h"
#include "amd64.h"
#include "spinlock.h"
#include "condvar.h"
#include "queue.h"
#include "proc.hh"
#include "cpu.hh"
#include "bits.hh"
#include "kmtrace.hh"
#include "kalloc.hh"
#include "vm.hh"
#include "ns.hh"
#include "wq.hh"
#include <uk/fcntl.h>
#include <uk/unistd.h>

u64
proc::hash(const u32 &p)
{
  return p;
}

xns<u32, proc*, proc::hash> *xnspid __mpalign__;
struct proc *bootproc __mpalign__;

#if MTRACE
struct kstack_tag kstack_tag[NCPU];
#endif

enum { sched_debug = 0 };

proc::proc(int npid) :
  rcu_freed("proc", this, sizeof(*this)), vmap(0), kstack(0),
  pid(npid), parent(0), tf(0), context(0), killed(0),
  ftable(0), tsc(0), curcycles(0), cpuid(0), fpu_state(nullptr),
  cpu_pin(0), oncv(0), cv_wakeup(0),
  futex_lock("proc::futex_lock", LOCKSTAT_PROC),
  user_fs_(0), unmap_tlbreq_(0), data_cpuid(-1), in_exec_(0), 
  uaccess_(0), yield_(false), upath(0), uargv(userptr<const char>(nullptr)),
  exception_inuse(0), magic(PROC_MAGIC), unmapped_hint(0), state_(EMBRYO)
{
  snprintf(lockname, sizeof(lockname), "cv:proc:%d", pid);
  lock = spinlock(lockname+3, LOCKSTAT_PROC);
  cv = condvar(lockname);
  gc = new gc_handle();
  memset(&childq, 0, sizeof(childq));
  memset(&child_next, 0, sizeof(child_next));
  memset(&cv_waiters, 0, sizeof(cv_waiters));
  memset(&cv_sleep, 0, sizeof(cv_sleep));
  memset(__cxa_eh_global, 0, sizeof(__cxa_eh_global));
}

proc::~proc(void)
{
  magic = 0;
  if (fpu_state)
    kmfree(fpu_state, FXSAVE_BYTES);
  fpu_state = nullptr;
  // delete gc;
}

void
proc::set_state(enum procstate s)
{
  switch(state_) {
  case EMBRYO:
    if (s != RUNNABLE)
      panic("EMBRYO -> %u", s);
    break;
  case SLEEPING:
    if (s != RUNNABLE)
      panic("SLEEPING -> %u", s);
    break;
  case RUNNABLE:
    if (s != RUNNING && s != RUNNABLE)
      panic("RUNNABLE -> %u", s);
    break;
  case RUNNING:
    if (s != RUNNABLE && s != SLEEPING && s != ZOMBIE)
      panic("RUNNING -> %u", s);
    break;
  case ZOMBIE:
    panic("ZOMBIE -> %u", s);
  }
  state_ = s;
}

int
proc::set_cpu_pin(int cpu)
{
  if (cpu < -1 || cpu >= ncpu)
    return -1;

  acquire(&lock);
  if (myproc() != this)
    panic("set_cpu_pin not implemented for non-current proc");
  if (cpu == -1) {
    cpu_pin = 0;
    release(&lock);
    return 0;
  }
  // Since we're the current proc, there's no runq to get off.
  // post_swtch will put us on the new runq.
  cpuid = cpu;
  cpu_pin = 1;
  myproc()->set_state(RUNNABLE);
  sched();
  assert(mycpu()->id == cpu);
  return 0;
}

// Give up the CPU for one scheduling round.
void
yield(void)
{
  acquire(&myproc()->lock);  //DOC: yieldlock
  myproc()->set_state(RUNNABLE);
  myproc()->yield_ = false;
  sched();
}


// A fork child's very first scheduling by scheduler()
// will swtch here.  "Return" to user space.
void
forkret(void)
{
  post_swtch();

  // Just for the first process. can't do it earlier
  // b/c file system code needs a process context
  // in which to call condvar::sleep().
  if(myproc()->cwd == nullptr) {
    mtstart(forkret, myproc());
    myproc()->cwd = namei(myproc()->cwd, "/");
    mtstop(myproc());
  }

  if (myproc()->cwd_m == nullptr)
    myproc()->cwd_m = namei(myproc()->cwd_m, "/");

  // Return to "caller", actually trapret (see allocproc).
}

// Exit the current process.  Does not return.
// An exited process remains in the zombie state
// until its parent calls wait() to find out it exited.
void
exit(void)
{
  struct proc *p, *np;
  int wakeupinit;

  if(myproc() == bootproc)
    panic("init exiting");

  if (myproc()->ftable)
    myproc()->ftable->decref();

  // Kernel threads might not have a cwd
  if (myproc()->cwd != nullptr)
      myproc()->cwd.reset();

  // Pass abandoned children to init.
  wakeupinit = 0;
  SLIST_FOREACH_SAFE(p, &(myproc()->childq), child_next, np) {
    acquire(&p->lock);
    p->parent = bootproc;
    if(p->get_state() == ZOMBIE)
      wakeupinit = 1;
    SLIST_REMOVE(&(myproc()->childq), p, proc, child_next);
    release(&p->lock);

    acquire(&bootproc->lock);
    SLIST_INSERT_HEAD(&bootproc->childq, p, child_next);
    release(&bootproc->lock);
  }

  // Lock the parent first, since otherwise we might deadlock.
  if (myproc()->parent != nullptr)
    acquire(&myproc()->parent->lock);

  acquire(&(myproc()->lock));

  // Kernel threads might not have a parent
  if (myproc()->parent != nullptr) {
    release(&myproc()->parent->lock);
    myproc()->parent->cv.wake_all();
  } else {
    idlezombie(myproc());
  }

  if (wakeupinit)
    bootproc->cv.wake_all();

  // Clean up FPU state
  if (myproc()->fpu_state) {
    // Make sure no CPUs think this process is the FPU owner
    for (int i = 0; i < ncpu; ++i) {
      struct proc *copy = myproc();
      atomic_compare_exchange_strong(&cpus[i].fpu_owner, &copy, (proc*)nullptr);
    }
  }

  // Jump into the scheduler, never to return.
  myproc()->set_state(ZOMBIE);
  sched();
  panic("zombie exit");
}

static void
freeproc(struct proc *p)
{
  gc_delayed(p);
}

void
execstub(void)
{
  userptr<userptr<char> const> uargv;
  const char* upath;

  upath = myproc()->upath;
  uargv = myproc()->uargv;
  barrier();
  myproc()->upath = nullptr;

  post_swtch();

  long r = doexec(upath, uargv);
  myproc()->tf->rax = r;

  // This stuff would have been called in syscall and syscall_c
  // if we returned from the the previous kstack

  mtstop(myproc());
  mtign();

  if (myproc()->killed) {
    mtstart(trap, myproc());
    exit();
  } 
}

static void
kstackfree(void* kstack)
{
  ksfree(slab_stack, kstack);
}

void
execswitch(proc* p)
{
  // Alloc a new kernel stack, set it up, and free the old one
  context* cntxt;
  trapframe* tf;
  char* kstack;
  char* sp;

  if ((kstack = (char*) ksalloc(slab_stack)) == 0)
    panic("execswitch: ksalloc");
  
  sp = kstack + KSTACKSIZE;
  sp -= sizeof(*p->tf);
  tf = (trapframe*)sp;
  // XXX(sbw) we only need the whole tf if exec fails
  *tf = *p->tf;

  sp -= 8;
  // XXX(sbw) we could use the sysret return path
  *(u64*)sp = (u64)trapret;
  sp -= sizeof(*p->context);
  cntxt = (context*)sp;
  memset(cntxt, 0, sizeof(*cntxt));
  cntxt->rip = (uptr)execstub;

  cwork* w = new cwork();
  if (w != nullptr) {
    w->rip = (void*) kstackfree;
    w->arg0 = p->kstack;
    if (wqcrit_push(w, p->data_cpuid) < 0) {
      ksfree(slab_stack, p->kstack);
      delete w;
    }
  } else {
    ksfree(slab_stack, p->kstack);
  }

  p->kstack = kstack;
  p->context = cntxt;
  p->tf = tf;
}

proc*
proc::alloc(void)
{
  char *sp;
  proc* p;

  p = new proc(xnspid->allockey());
  if (p == nullptr)
    throw_bad_alloc();

  p->cpuid = mycpu()->id;
#if MTRACE
  p->mtrace_stacks.curr = -1;
#endif

  if (!xnspid->insert(p->pid, p))
    panic("allocproc: ns_insert");

  // Allocate kernel stack if possible.
  if((p->kstack = (char*) ksalloc(slab_stack)) == 0){
    if (!xnspid->remove(p->pid, &p))
      panic("allocproc: ns_remove");
    freeproc(p);
    return 0;
  }

  sp = p->kstack + KSTACKSIZE;
  
  // Leave room for trap frame.
  sp -= sizeof *p->tf;
  p->tf = (struct trapframe*)sp;

  // amd64 ABI mandates sp % 16 == 0 before a call instruction
  // (or after executing a ret instruction)
  if ((uptr) sp % 16)
    panic("allocproc: misaligned sp");

  // Set up new context to start executing at forkret,
  // which returns to trapret.
  sp -= 8;
  *(u64*)sp = (u64)trapret;

  sp -= sizeof *p->context;
  p->context = (struct context*)sp;
  memset(p->context, 0, sizeof *p->context);
  p->context->rip = (uptr)forkret;

  return p;
}

void
initproc(void)
{
  xnspid = new xns<u32, proc*, proc::hash>(false);
  if (xnspid == 0)
    panic("pinit");
}

// Kill the process with the given pid.
// Process won't exit until it returns
// to user space (see trap in trap.c).
int
proc::kill(void)
{
  acquire(&lock);
  killed = 1;
  if(get_state() == SLEEPING) {
    // XXX
    // we need to wake p up if it is condvar::sleep()ing.
    // can't change p from SLEEPING to RUNNABLE since that
    //   would make some condvar->waiters a dangling reference,
    //   and the non-zero p->cv_next will cause a future panic.
    // can't call p->oncv.wake_all() since that results in
    //   deadlock (addrun() acquires p->lock).
    // can't release p->lock then call wake_all() since the
    //   cv might be deallocated while we're using it
    //   (pipes dynamically allocate condvars).
  }
  release(&lock);
  return 0;
}

int
proc::kill(int pid)
{
  struct proc *p;

  p = xnspid->lookup(pid);
  if (p == 0) {
    panic("kill");
    return -1;
  }
  return p->kill();
}

// Print a process listing to console.  For debugging.
// Runs when user types ^P on console.
// No lock to avoid wedging a stuck machine further.
void
procdumpall(void)
{
  static const char *states[] = {
    /* [EMBRYO]   = */ "embryo",
    /* [SLEEPING] = */ "sleep ",
    /* [RUNNABLE] = */ "runble",
    /* [RUNNING]  = */ "run   ",
    /* [ZOMBIE]   = */ "zombie"
  };
  const char *name = "(no name)";
  const char *state;
  uptr pc[10];

  for (proc *p : xnspid) {
    if(p->get_state() >= 0 && p->get_state() < NELEM(states) && 
       states[p->get_state()])
      state = states[p->get_state()];
    else
      state = "???";
    
    if (p->name && p->name[0] != 0)
      name = p->name;
    
    cprintf("\n%-3d %-10s %8s %2u  %lu\n",
            p->pid, name, state, p->cpuid, p->tsc);
    
    if(p->get_state() == SLEEPING){
      getcallerpcs((void*)p->context->rbp, pc, NELEM(pc));
      for(int i=0; i<10 && pc[i] != 0; i++)
        cprintf(" %lx\n", pc[i]);
    }
  }
}

// Create a new process copying p as the parent.
// Sets up stack to return as if from system call.
// Caller must set state of returned proc to RUNNABLE.
int
fork(int flags)
{
  int pid;
  struct proc *np;

  //cprintf("%d: fork\n", myproc()->pid);

  // Allocate process.
  if((np = proc::alloc()) == 0)
    return -1;

  auto proc_cleanup = scoped_cleanup([&np]() {
    if (!xnspid->remove(np->pid, &np))
      panic("fork: ns_remove");
    freeproc(np);
  });

  if(flags & FORK_SHARE_VMAP) {
    np->vmap = myproc()->vmap;
    np->vmap->ref++;
  } else {
    // Copy process state from p.
    np->vmap = myproc()->vmap->copy();
  }

  np->parent = myproc();
  *np->tf = *myproc()->tf;
  np->cpu_pin = myproc()->cpu_pin;
  np->data_cpuid = myproc()->data_cpuid;
  np->run_cpuid_ = myproc()->run_cpuid_;
  np->user_fs_ = myproc()->user_fs_;

  // Clear %eax so that fork returns 0 in the child.
  np->tf->rax = 0;

  if (flags & FORK_SHARE_FD) {
    myproc()->ftable->incref();
    np->ftable = myproc()->ftable;
  } else {
    np->ftable = myproc()->ftable->copy();
  }

  np->cwd = myproc()->cwd;
  np->cwd_m = myproc()->cwd_m;
  pid = np->pid;
  safestrcpy(np->name, myproc()->name, sizeof(myproc()->name));
  acquire(&myproc()->lock);
  SLIST_INSERT_HEAD(&myproc()->childq, np, child_next);
  release(&myproc()->lock);

  acquire(&np->lock);
  np->cpuid = mycpu()->id;
  addrun(np);
  release(&np->lock);

  proc_cleanup.dismiss();
  return pid;
}

void
finishproc(struct proc *p, bool removepid)
{
  if (removepid && !xnspid->remove(p->pid, &p))
    panic("finishproc: ns_remove");
  if (p->vmap != nullptr)
    p->vmap->decref();
  if (p->kstack)
    ksfree(slab_stack, p->kstack);

  p->pid = 0;
  p->parent = 0;
  p->name[0] = 0;
  p->killed = 0;
  freeproc(p);
#if DEBUG
  gc_wakeup();
#endif
}

// Wait for a child process to exit and return its pid.
// Return -1 if this process has no children.
int
wait(int wpid)
{
  struct proc *p, *np;
  int havekids, pid;

  for(;;){
    // Scan children for ZOMBIEs
    havekids = 0;
    acquire(&myproc()->lock);
    SLIST_FOREACH_SAFE(p, &myproc()->childq, child_next, np) {
      acquire(&p->lock);
      if (wpid == -1 || wpid == p->pid) {
	havekids = 1;
	if(p->get_state() == ZOMBIE){
	  release(&p->lock);	// noone else better be trying to lock p
	  pid = p->pid;
	  SLIST_REMOVE(&myproc()->childq, p, proc, child_next);
	  release(&myproc()->lock);

          if (!xnspid->remove(pid, &p))
            panic("wait: ns_remove");

          cwork *w = new cwork();
          assert(w);
          w->rip = (void*) finishproc;
          w->arg0 = p;
          w->arg1 = 0;
          if (wqcrit_push(w, p->run_cpuid_) < 0) {
            delete w;
            finishproc(p, 0);
          }
	  return pid;
	}
      }
      release(&p->lock);
    }

    // No point waiting if we don't have any children.
    if(!havekids || myproc()->killed){
      release(&myproc()->lock);
      return -1;
    }

    // Wait for children to exit.  (See wakeup1 call in proc_exit.)
    myproc()->cv.sleep(&myproc()->lock);

    release(&myproc()->lock);
  }
}

void
threadhelper(void (*fn)(void *), void *arg)
{
  post_swtch();
  mtstart(fn, myproc());
  fn(arg);
  exit();
}

struct proc*
threadalloc(void (*fn)(void *), void *arg)
{
  struct proc *p;

  p = proc::alloc();
  if (p == nullptr)
    return 0;

  auto proc_cleanup = scoped_cleanup([&p]() {
    if (!xnspid->remove(p->pid, &p))
      panic("fork: ns_remove");
    freeproc(p);
  });

  p->vmap = vmap::alloc();
  if (p->vmap == nullptr)
    return 0;

  p->context->rip = (u64)threadstub;
  p->context->r12 = (u64)fn;
  p->context->r13 = (u64)arg;
  p->parent = nullptr;
  p->cwd.reset();

  proc_cleanup.dismiss();
  return p;
}

struct proc*
threadpin(void (*fn)(void*), void *arg, const char *name, int cpu)
{
  struct proc *p;

  p = threadalloc(fn, arg);
  if (p == nullptr)
    panic("threadpin: alloc");

  snprintf(p->name, sizeof(p->name), "%s", name);
  p->cpuid = cpu;
  p->cpu_pin = 1;
  acquire(&p->lock);
  addrun(p);
  release(&p->lock);
  return p;
}
