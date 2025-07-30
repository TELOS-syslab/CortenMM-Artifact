#include <atomic>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/types.h>

#include "libutil.h"
#include "amd64.h"
#include "rnd.hh"
#include "xsys.h"

#if !defined(XV6_USER)
#include <pthread.h>
#include <sys/wait.h>
#else
#include "types.h"
#include "user.h"
#include "pthread.h"
#include "bits.hh"
#include "kstats.hh"
#endif

#if defined(XV6_USER) && defined(HW_ben)
int get_cpu_order(int thread)
{
  const int cpu_order[] = {
    // Socket 0
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
    // Socket 1
    10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
    // Socket 3
    30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
    // Socket 2
    20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
    // Socket 5
    50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
    // Socket 4
    40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
    // Socket 6
    60, 61, 62, 63, 64, 65, 66, 67, 68, 69,
    // Socket 7
    70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
  };

  return cpu_order[thread];
}
#else
int get_cpu_order(int thread)
{
  return thread;
}
#endif

long get_time_in_nanos(long start_tsc, long end_tsc)
{
	// Our setup is a 1.9 GHz CPU
	return (end_tsc - start_tsc) * 10 / 19;
}

unsigned int simple_get_rand(unsigned int last_rand)
{
	return ((long)last_rand * 1103515245 + 12345) & 0x7fffffff;
}

size_t up_align(size_t size, size_t alignment)
{
	return ((size) + ((alignment) - 1)) & ~((alignment) - 1);
}

#define PAGE_SIZE 4096
#define NUM_PAGES (1<<18) // 1G

static pthread_barrier_t bar0, bar1;

typedef struct {
	char *region;
	size_t pages;
    int thread_id;
    int num_threads;
} thread_data_t;

pthread_t threads[128];
thread_data_t thread_data[128];

void *worker_thread(void *arg)
{
	thread_data_t *data = (thread_data_t *)arg;

    if (setaffinity(get_cpu_order(data->thread_id)) < 0) {
		die("setaffinity err");
		exit(EXIT_FAILURE);
	}

    // Trigger page fault
	for (size_t i = 0; i < data->pages; i++) {
        data->region[i * PAGE_SIZE] = 1;
	}

    pthread_barrier_wait(&bar0);
    if (data->thread_id == 0) {
        printf("%d, %lu, %lu\n", data->num_threads, pt_pages(), radix_size());
    }
	pthread_barrier_wait(&bar1);

	// Barrier at here. Output pagetable size and vma tree size.

	return NULL;
}

void run_test(size_t num_threads)
{
    pthread_barrier_init(&bar0, 0, num_threads);
    pthread_barrier_init(&bar1, 0, num_threads);

	char *region = (char*)mmap(0, NUM_PAGES * PAGE_SIZE, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
	if (region == MAP_FAILED) {
		die("mmap failed");
		exit(EXIT_FAILURE);
	}

    size_t pages_per_thread = NUM_PAGES / num_threads;

	for (size_t i = 0; i < num_threads; i++) {
        thread_data[i].region = region + i * pages_per_thread * PAGE_SIZE;
        thread_data[i].pages = pages_per_thread;
        thread_data[i].thread_id = i;
        thread_data[i].num_threads = num_threads;
        if (xthread_create(&threads[i], 0, worker_thread,
				   &thread_data[i]) != 0) {
			die("pthread_create failed");
			exit(EXIT_FAILURE);
		}
	}

    // Join threads
	for (int i = 0; i < num_threads; i++) {
		xpthread_join(threads[i]);
	}

    munmap(region, NUM_PAGES * PAGE_SIZE);
}

void run_test_forked(size_t num_threads)
{
    // Spawn a process for a test in order to avoid interference between tests
	int pid = xfork();
	if (pid == -1) {
		die("fork failed");
		exit(EXIT_FAILURE);
	} else if (pid == 0) {
		// Child process
		run_test(num_threads);
		exit(EXIT_SUCCESS);
	} else {
		// Parent process
		wait(pid);
	}
}

int main(int argc, char *argv[])
{
	printf("Threads, PT pages, Radix tree size\n");

	int num_threads;
	if (argc == 1) {
		num_threads = -1;
	} else if (argc == 2) {
		num_threads = atoi(argv[1]);
	} else {
		fprintf(stderr, "Usage: %s [num_threads]\n", argv[0]);
		exit(EXIT_FAILURE);
	}

	if (num_threads == -1) {
		int threads[] = { 1, 2, 4, 8, 16, 32, 48, 64, 80, 96, 112, 128 };
		for (int i = 0; i < sizeof(threads) / sizeof(int); i++) {
			run_test_forked(threads[i]);
		}
	} else {
		run_test_forked(num_threads);
	}

	return 0;
}
