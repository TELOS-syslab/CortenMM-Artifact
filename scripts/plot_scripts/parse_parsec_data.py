from common import SYS_ADV, SYS_RW, LINUX, find_and_read_latest_experiment_output

import os
import re

def parse_input():
    systems_data_raw = {
        SYS_ADV: find_and_read_latest_experiment_output("macrometis", "corten-adv"),
        SYS_RW: find_and_read_latest_experiment_output("macrometis", "corten-rw"),
        LINUX: find_and_read_latest_experiment_output("macrometis", "linux"),
        "RadixVM": find_and_read_latest_experiment_output("macrometis", "radixvm"),
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
                    # Extract application name
                    app_match = re.search(r'Running application:\s*(\w+)', block_data)
                    if not app_match:
                        continue
                    app_name = app_match.group(1)

                    # Extract thread count and tput
                    match = re.search(r'\[Result Summary\](\d+),\s*(\d+)', block_data)
                    
                    if match:
                        thread_count = int(match.group(1))
                        tput = int(match.group(2)) / 60  # Convert to jobs/min
                        
                        if app_name == "ferret" or app_name == "x264":
                            continue
                        # Initialize app data structure if not present
                        if app_name not in systems_data:
                            systems_data[app_name] = {}
                        if system not in systems_data[app_name]:
                            systems_data[app_name][system] = {}

                        # Store the finish time for this thread count
                        systems_data[app_name][system][thread_count] = tput

    return systems_data
