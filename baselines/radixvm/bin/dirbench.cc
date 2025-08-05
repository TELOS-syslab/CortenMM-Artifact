#if defined(LINUX)
#include "user/util.h"
#include "types.h"
#include <unistd.h>
#include <assert.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include "xsys.h"
#else
#include "types.h"
#include "user.h"
#include "mtrace.h"
#include "amd64.h"
#include "xsys.h"
#endif
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

static const bool pinit = true;

enum { nfile = MTRACE ? 2 : 10 };
enum { nlookup = MTRACE ? 2 : 100 };

// XXX(austin) Totally lame.  Put this buffer in the BSS so we don't
// have to COW fault the stack.
static char pn[32]
__attribute__((aligned(4096)));

void
bench(u32 tid, int nloop, const char* path)
{
//  char pn[32];

  if (pinit)
    setaffinity(tid);

  for (u32 x = 0; x < nloop; x++) {
    for (u32 i = 0; i < nfile; i++) {
      snprintf(pn, sizeof(pn), "%s/f:%d:%d", path, tid, i);

      int fd = open(pn, O_CREAT|O_RDWR, S_IRUSR|S_IWUSR);
      if (fd < 0)
	die("create failed\n");

      close(fd);
    }

    for (u32 i = 0; i < nlookup; i++) {
      snprintf(pn, sizeof(pn), "%s/f:%d:%d", path, tid, (i % nfile));
      int fd = open(pn, O_RDWR);
      if (fd < 0)
        die("open failed %s", pn);

      close(fd);
    }

    for (u32 i = 0; i < nfile; i++) {
      snprintf(pn, sizeof(pn), "%s/f:%d:%d", path, tid, i);
      if (unlink(pn) < 0)
	die("unlink failed\n");
    }
  }

  exit(0);
}

int
main(int ac, char** av)
{
  const char* path;
  int nthread;
  int nloop;
  
#ifdef HW_qemu
  nloop = 50;
#else
  nloop = 1000;
#endif
  path = "/dbx";

  if (ac < 2)
    die("usage: %s nthreads [nloop] [path]", av[0]);

  nthread = atoi(av[1]);
  if (ac > 2)
    nloop = atoi(av[2]);
  if (ac > 3)
    path = av[3];

  mkdir(path, 0777);

  mtenable_type(mtrace_record_ascope, "xv6-dirbench");

  u64 t0 = rdtsc();
  for(u32 i = 0; i < nthread; i++) {
    int pid = xfork();
    if (pid == 0) {
      bench(i, nloop, path);
    } else if (pid < 0)
      die("fork");
  }

  for (u32 i = 0; i < nthread; i++)
    xwait();
  u64 t1 = rdtsc();
  mtdisable("xv6-dirbench");

  printf("dirbench: %lu\n", t1-t0);
  return 0;
}
