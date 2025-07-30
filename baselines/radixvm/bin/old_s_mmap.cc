#include "old_scale_common.h"

#define NUM_MMAPS 512 // Number mmaps per thread

char * const base = (char*)0x100000000UL;

void *worker_thread(void *arg)
{
	thread_data_t *data = (thread_data_t *)arg;

    if (setaffinity(get_cpu_order(data->thread_id)) < 0) {
		die("setaffinity err");
		exit(EXIT_FAILURE);
	}

	long tsc_start, tsc_end;

	// Wait for that all threads are ready
	pthread_barrier_wait(&bar);

	tsc_start = rdtsc();

	// map them one by one
	char *p = base + (size_t)data->thread_id * NUM_MMAPS * 8 * 0x100000;
	for (size_t i = 0; i < NUM_MMAPS; i++) {
		mmap((char*)(p + i * PAGE_SIZE * 8), PAGE_SIZE * 8, PROT_READ | PROT_WRITE,
				 MAP_PRIVATE | MAP_FIXED | MAP_ANONYMOUS, -1, 0);
	}

	tsc_end = rdtsc();
	long tot_time = get_time_in_nanos(tsc_start, tsc_end);

	data->lat = tot_time / NUM_MMAPS;

	return NULL;
}

int main(int argc, char *argv[])
{
	return entry_point(argc, argv, worker_thread,
			   (test_config_t){ .num_prealloc_pages_per_thread = 1,
					    .trigger_fault_before_spawn = 0, .rand_assign_pages = 0 });
}