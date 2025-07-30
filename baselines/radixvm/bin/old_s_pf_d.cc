#include "old_scale_common.h"

#define NUM_PAGES 1024 // Number of pages to allocate per thread for mmap

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

	char *region = data->region + data->thread_id * NUM_PAGES * PAGE_SIZE;
	for (size_t i = 0; i < NUM_PAGES; i++) {
		region[i * PAGE_SIZE] = 1; // Trigger page fault
	}

	tsc_end = rdtsc();
	long tot_time = get_time_in_nanos(tsc_start, tsc_end);

	data->lat = tot_time / NUM_PAGES;

	return NULL;
}

int main(int argc, char *argv[])
{
	return entry_point(argc, argv, worker_thread,
			   (test_config_t){ .num_prealloc_pages_per_thread =
						    NUM_PAGES,
					    .trigger_fault_before_spawn = 0, .rand_assign_pages = 0 });
}
