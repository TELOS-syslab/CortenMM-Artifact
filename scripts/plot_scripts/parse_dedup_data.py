from common import LINUX_TC, SYS_ADV_PT, SYS_RW_PT, LINUX_PT, LINUX_TC, SYS_ADV_TC, SYS_RW_TC, SYS_DVA, SYS_BASE, find_and_read_latest_experiment_output

import os
import re

def parse_input():
    systems_data_raw = {
        SYS_ADV_PT: find_and_read_latest_experiment_output("macrodedup", "corten-adv_pt"),
        SYS_RW_PT: find_and_read_latest_experiment_output("macrodedup", "corten-rw_pt"),
        LINUX_PT: find_and_read_latest_experiment_output("macrodedup", "linux_pt"),
        LINUX_TC: find_and_read_latest_experiment_output("macrodedup", "linux_tc"),
        SYS_ADV_TC: find_and_read_latest_experiment_output("macrodedup", "corten-adv_tc"),
        SYS_DVA: find_and_read_latest_experiment_output("macrodedup", "corten-adv-dva"),
        SYS_BASE: find_and_read_latest_experiment_output("macrodedup", "corten-base"),
    }

    systems_data = {}
    for system, content in systems_data_raw.items():
        # Initialize system data structure
        system_data = {}
        systems_data[system] = {}

        if content is None:
            continue

        # Find all benchmark blocks
        blocks = re.split(r'\*\*\*(.*?)\*\*\*', content)
        # Skip first element (content before first benchmark)
        blocks = blocks[1:]
        # Process in pairs (name, data)
        for i in range(0, len(blocks), 2):
            if i + 1 < len(blocks):
                block_type = blocks[i].strip()
                block_data = blocks[i+1].strip()
                
                # Only process TEST_START blocks
                if block_type == "TEST_START":
                    # Extract thread count and tput
                    match = re.search(r'\[Result Summary\](\d+),\s*(\d+)', block_data)

                    if match:
                        thread_count = int(match.group(1))
                        tput = int(match.group(2)) / 60  # Convert to jobs/min
                        
                        # Store the finish time for this thread count
                        system_data[thread_count] = tput
        
        systems_data[system] = system_data

    return systems_data
