from common import LINUX_TC, SYS_ADV_PT, SYS_RW_PT, LINUX_PT, LINUX_TC, SYS_ADV_TC, SYS_RW_TC, SYS_DVA, SYS_BASE, find_and_read_latest_experiment_output

import os
import re

def parse_input():
    systems_data_raw = {
        SYS_ADV_PT: find_and_read_latest_experiment_output("macropsearchy", "corten-adv_pt"),
        SYS_RW_PT: find_and_read_latest_experiment_output("macropsearchy", "corten-rw_pt"),
        LINUX_PT: find_and_read_latest_experiment_output("macropsearchy", "linux_pt"),
        LINUX_TC: find_and_read_latest_experiment_output("macropsearchy", "linux_tc"),
        SYS_ADV_TC: find_and_read_latest_experiment_output("macropsearchy", "corten-adv_tc"),
        SYS_DVA: find_and_read_latest_experiment_output("macropsearchy", "corten-adv-dva"),
        SYS_BASE: find_and_read_latest_experiment_output("macropsearchy", "corten-base"),
    }

    systems_data = {}
    for system, content in systems_data_raw.items():
        # Initialize system data structure
        system_data = {}

        if content is None:
            systems_data[system] = {}
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
                    match = re.search(r'^(\d+):.*?total throughput:\s*(\d+(?:\.\d+)?)\s*jobs/hour', block_data, re.MULTILINE | re.DOTALL)
                    
                    if match:
                        thread_count = int(match.group(1))
                        tput = float(match.group(2))
                        
                        # Store the finish time for this thread count
                        system_data[thread_count] = tput / 60.0  # Convert to jobs/min
        
        systems_data[system] = system_data

    return systems_data
