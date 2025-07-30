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
	return ((size) + ((alignment)-1)) & ~((alignment)-1);
}

#define PAGE_SIZE 4096 // Typical page size in bytes
// Single thread test, will be executed 4096 times;
// 8 thread test will be executed 512 times;
// 128 thread test will be excuted 32 times, etc.
// Statistics are per-thread basis.
#define TOT_THREAD_RUNS 4096

#define RESULT_FILE "results"

typedef struct {
	char *region;
	// For random tests
	int *page_idx;
	int thread_id;
	// Pass the result back to the main thread
	long lat;
} thread_data_t;

static pthread_barrier_t bar;

typedef struct {
	size_t num_prealloc_pages_per_thread;
	int trigger_fault_before_spawn;
	int rand_assign_pages;
} test_config_t;

// Decls

int entry_point(int argc, char *argv[], void *(*worker_thread)(void *),
		test_config_t config);
void run_test_specify_threads(int num_threads, void *(*worker_thread)(void *),
			      test_config_t config);
void run_test_specify_rounds(int num_threads, void *(*worker_thread)(void *),
			     test_config_t config);
void run_test_forked(int num_threads, void *(*worker_thread)(void *),
		     test_config_t config);
void run_test(int num_threads, void *(*worker_thread)(void *),
	      test_config_t config);

// Impls

int entry_point(int argc, char *argv[], void *(*worker_thread)(void *),
		test_config_t config)
{
	int num_threads;
	if (argc == 1) {
		num_threads = -1;
	} else if (argc == 2) {
		num_threads = atoi(argv[1]);
	} else {
		fprintf(stderr, "Usage: %s [num_threads]\n", argv[0]);
		exit(EXIT_FAILURE);
	}

	run_test_specify_threads(num_threads, worker_thread, config);

	return 0;
}

void run_test_specify_threads(int num_threads, void *(*worker_thread)(void *),
			      test_config_t config)
{
	printf("Threads, p5 lat (ns), Avg lat (ns), p95 lat (ns), Pos err lat (ns2), Neg err lat (ns2)\n");

	if (num_threads == -1) {
		int threads[] = { 1, 2, 4, 8, 16, 32, 48, 64, 80, 96, 112, 128 };
		for (int i = 0; i < sizeof(threads) / sizeof(int); i++) {
			run_test_specify_rounds(threads[i], worker_thread,
						config);
		}
	} else {
		run_test_specify_rounds(num_threads, worker_thread, config);
	}
}

pthread_t threads[TOT_THREAD_RUNS];
thread_data_t thread_data[TOT_THREAD_RUNS];
long thread_lat[TOT_THREAD_RUNS];

void run_test_specify_rounds(int num_threads, void *(*worker_thread)(void *),
			  test_config_t config)
{
	unlink(RESULT_FILE);

	int runs = TOT_THREAD_RUNS / num_threads;
	for (int run_id = 0; run_id < runs; run_id++) {
		run_test_forked(num_threads, worker_thread, config);
	}

	// Read latency data from RESULT_FILE
    int fd = open(RESULT_FILE, O_RDONLY);
	if (fd == -1) {
		die("open failed");
		exit(EXIT_FAILURE);
	}
	int tot_runs = 0;
	while (1) {
		long lat = 0;
		int r = read(fd, &lat, sizeof(lat));
		if (r<0) {
			close(fd);
			die("readline failed");
		}
		else if (r==0)
			break;
		else {
			thread_lat[tot_runs++] = lat;
		}
	}
	close(fd);

	if (tot_runs != num_threads * runs) {
		die("Incorrect number of runs");
		exit(EXIT_FAILURE);
	}

	// Calculate the p5, average, p95, and variance of the latencies
	long avg = 0;
	for (int i = 0; i < tot_runs; i++) {
		avg += thread_lat[i];
	}
	avg /= tot_runs;
	long posvar2 = 0;
	long numpos = 0;
	long negvar2 = 0;
	long numneg = 0;
	for (int i = 0; i < tot_runs; i++) {
		long diff = thread_lat[i] - avg;
		if (diff > 0) {
			posvar2 += diff * diff;
			numpos++;
		} else {
			negvar2 += diff * diff;
			numneg++;
		}
	}
	posvar2 /= numpos;
	negvar2 /= numneg;

	// Calculate the p5 and p95 latencies
	// bubble sort
	for (int i = 0; i < tot_runs; i++) {
		for (int j = i + 1; j < tot_runs; j++) {
			if (thread_lat[i] > thread_lat[j]) {
				long temp = thread_lat[i];
				thread_lat[i] = thread_lat[j];
				thread_lat[j] = temp;
			}
		}
	}
	long p5 = thread_lat[tot_runs / 20];
	long p95 = thread_lat[tot_runs * 19 / 20];

	printf("%d, %ld, %ld, %ld, %ld, %ld\n", num_threads, p5, avg, p95,
	       posvar2, negvar2);
}

void run_test_forked(int num_threads, void *(*worker_thread)(void *),
		     test_config_t config)
{
	// Spawn a process for a test in order to avoid interference between tests
	int pid = xfork();
	if (pid == -1) {
		die("fork failed");
		exit(EXIT_FAILURE);
	} else if (pid == 0) {
		// Child process
		run_test(num_threads, worker_thread, config);
		exit(EXIT_SUCCESS);
	} else {
		// Parent process
		wait(NULL);
	}
}

void run_test(int num_threads, void *(*worker_thread)(void *),
	      test_config_t config)
{
	size_t num_prealloc_pages = config.num_prealloc_pages_per_thread;
	size_t num_tot_pages = num_prealloc_pages * num_threads;
	int trigger_fault_before_spawn = config.trigger_fault_before_spawn;
	int rand_assign_pages = config.rand_assign_pages;

	pthread_barrier_init(&bar, 0, num_threads);

	char *region = (char *)mmap(0, num_tot_pages * PAGE_SIZE,
			    PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS,
			    -1, 0);

	if (region == MAP_FAILED) {
		die("mmap failed");
		exit(EXIT_FAILURE);
	}

	if (trigger_fault_before_spawn) {
		// Trigger page faults before spawning threads
		for (int i = 0; i < num_tot_pages; i++) {
			region[i * PAGE_SIZE] = 1;
		}
	}

	int *page_idx = NULL;
	int page_idx_size = 0;
	if (rand_assign_pages) {
		page_idx_size =
			up_align(num_tot_pages * sizeof(int), PAGE_SIZE);
		page_idx = (int *)mmap(0, page_idx_size, PROT_READ | PROT_WRITE,
				MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
		for (int i = 0; i < num_tot_pages; i++) {
			page_idx[i] = i;
		}

		// Random shuffle
		unsigned int rand = 0xdeadbeef - num_threads;
		for (int i = num_tot_pages - 1; i > 0; i--) {
			rand = simple_get_rand(rand);
			int j = rand % (i + 1);
			int temp = page_idx[i];
			page_idx[i] = page_idx[j];
			page_idx[j] = temp;
		}
	}

	// Create threads and trigger page faults in parallel
	for (int i = 0; i < num_threads; i++) {
		thread_data[i].region = region;
		thread_data[i].page_idx = page_idx;
		thread_data[i].thread_id = i;

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

	// munmap(region, num_tot_pages * PAGE_SIZE);
	// if (rand_assign_pages) {
	// 	munmap(page_idx, page_idx_size);
	// }

	// Write latency data to RESULT_FILE
    int fd = open(RESULT_FILE, O_RDWR | O_APPEND | O_CREAT, 0666);
	if (fd == -1) {
		die("open failed");
		exit(EXIT_FAILURE);
	}

	for (int i = 0; i < num_threads; i++) {
		write(fd, &(thread_data[i].lat), sizeof(thread_data[i].lat));
	}
	close(fd);
}