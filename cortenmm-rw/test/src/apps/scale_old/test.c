#include "common.h"

#define NUM_FRAMES 64 // Number of frames (pages) to map/unmap per iteration
#define NUM_ITERATIONS 100 // Number of iterations in the tight loop

int main(int argc, char *argv[])
{
	long num_tests = 0, tot_map_time = 0, tot_pf_time = 0,
	     tot_unmap_time = 0;

	for (;; num_tests++) {
		// Tight loop: map 64 frames, trigger page faults, unmap them
		for (int iter = 0; iter < NUM_ITERATIONS; iter++) {
			char *mapped_pages;

			long tsc_start = rdtsc();
			// Map 64 frames (pages)
			mapped_pages = mmap(NULL, PAGE_SIZE * NUM_FRAMES,
					    PROT_READ | PROT_WRITE,
					    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
			long map_tsc_time =
				get_time_in_nanos(tsc_start, rdtsc());
			if (mapped_pages == MAP_FAILED) {
				perror("mmap failed");
				exit(EXIT_FAILURE);
			}
			tot_map_time += map_tsc_time;

			tsc_start = rdtsc();
			// Trigger page faults on all mapped frames
			for (int i = 0; i < NUM_FRAMES; i++) {
				*(int *)(mapped_pages + i * PAGE_SIZE) =
					i * iter; // Write to trigger page fault
			}
			tot_pf_time += get_time_in_nanos(tsc_start, rdtsc());

			tsc_start = rdtsc();
			int unmap_ret =
				munmap(mapped_pages, PAGE_SIZE * NUM_FRAMES);
			long unmap_tsc_time =
				get_time_in_nanos(tsc_start, rdtsc());
			// Unmap all frames
			if (unmap_ret != 0) {
				perror("munmap failed");
				exit(EXIT_FAILURE);
			}
			tot_unmap_time += unmap_tsc_time;
		}

		if (num_tests % 100 == 0) {
			printf("Average time for mapping: %ld ns\n",
			       tot_map_time / (100 * NUM_ITERATIONS));
			printf("Average time for page faults: %ld ns\n",
			       tot_pf_time / (100 * NUM_ITERATIONS) /
				       NUM_FRAMES);
			printf("Average time for unmapping: %ld ns\n",
			       tot_unmap_time / (100 * NUM_ITERATIONS));

			tot_map_time = 0;
			tot_pf_time = 0;
			tot_unmap_time = 0;
		}
	}
}