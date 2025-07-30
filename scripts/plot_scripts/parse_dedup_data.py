from common import LINUX_TC, SYS_ADV_PT, SYS_RW_PT, LINUX_PT, LINUX_TC, SYS_ADV_TC, SYS_RW_TC, SYS_DVA, SYS_BASE

import os
import re

def parse_input():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    data_dir = os.path.join(script_dir, "../data/macro/dedup/")
    systems_data_raw_file = {
        SYS_ADV_PT: "aster-rcu.txt",
        SYS_RW_PT: "aster-rwl.txt",
        LINUX_PT: "linux-6.13.8.txt",
        LINUX_TC: "linux-tc.txt",
        SYS_ADV_TC: "aster-rcu-tc.txt",
        SYS_DVA: "adv-vpa.txt",
        SYS_BASE: "base.txt",
    }
    systems_data_raw = { k: os.path.join(data_dir, v) for k, v in systems_data_raw_file.items() }

    systems_data = {}
    for system, data_path in systems_data_raw.items():
        # Initialize system data structure
        system_data = {}

        try:
            with open(data_path, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Warning: File {data_path} not found. Skipping {system}.")
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
                    match = re.search(r'\[Result Summary\](\d+),\s*(\d+)', block_data)

                    if match:
                        thread_count = int(match.group(1))
                        tput = int(match.group(2)) / 60  # Convert to jobs/min
                        
                        # Store the finish time for this thread count
                        system_data[thread_count] = tput
        
        systems_data[system] = system_data

    return systems_data
