#include "types.h"
#include "user.h"
#include "amd64.h"
#include "pmc.hh"
#include "bits.hh"
#include <stdio.h>

#define CMN PERF_SEL_USR|PERF_SEL_OS|PERF_SEL_ENABLE

struct selector {
  const char* name;
  u64 sel;
};

static struct selector pmc_selector[] = {
  { "not halted",      CMN|0x76 },
  { "remote probes",   CMN|(0x4|0x8)<<8|0xec },
  { "L2 misses",       CMN|(0x2|0x8)<<8|0x7e },
  { "MAB requests",    CMN|(0x1)<<8|0x68 },
  { "MAB cycles",      CMN|(0x1)<<8|0x69 },
};

static const char*
valstr(u64 val)
{
  static char buf[32];

  if (val > 10*1000*1000*1000UL)
    snprintf(buf, sizeof(buf), "%lu G", val/(1000*1000*1000));
  else if (val > 10*1000*1000)
    snprintf(buf, sizeof(buf), "%lu M", val/(1000*1000));
  else if (val > 10*1000)
    snprintf(buf, sizeof(buf), "%lu k", val/1000);
  else
    snprintf(buf, sizeof(buf), "%lu", val);    

  return buf;
}

int
main(int ac, char * const av[])
{
  char * const *xav;
  int pmci = 0;

  xav = &av[1];
  if (xav[0][0] == '-') {
    pmci = atoi(&xav[0][1]);
    xav = &xav[1];
  }

  sys_stat* s0 = sys_stat::read();
  pmc_count::config(pmc_selector[pmci].sel);
  pmc_count pmc0 = pmc_count::read(0);
  u64 t0 = rdtsc();

  int pid = fork(0);
  if (pid < 0)
    die("xtime: fork failed");
  
  if (pid == 0) {
    execv(xav[0], xav);
    die("xtime: exec failed");
  }

  wait(-1);
  sys_stat* s1 = sys_stat::read();
  pmc_count pmc1 = pmc_count::read(0);
  u64 t1 = rdtsc();
  sys_stat* s2 = s1->delta(s0);

  printf("%s cycles\n", valstr(t1-t0));
  printf("%s %s\n", valstr(pmc1.delta(pmc0).sum()),
         pmc_selector[pmci].name);

  u64 tot = s2->busy() + s2->idle();
  printf(".%lu idle\n", (s2->idle()*100)/tot);
  return 0;
}
