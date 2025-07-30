from common import SYS_ADV, SYS_RW, SYS_BASE, SYS_DVA

import os
import re

def finish_time_to_tput(finish_time):
    """
    Convert finish time to throughput.
    :param finish_time: Finish time in milliseconds.
    :return: Throughput in operations per minutes.
    """
    return (60 * 1e3) / finish_time

def parse_input():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    data_dir = os.path.join(script_dir, "../data/macro/metis/")
    systems_data_raw_file = {
        SYS_ADV: "aster-rcu.txt",
        SYS_RW: "aster-rwlock.txt",
        "Linux": "linux-6.13.8.txt",
        "RadixVM": "radixvm.txt",
        "NrOS": "well we didn't run",
        SYS_DVA: "dva.txt",
        SYS_BASE: "base.txt",
    }
    systems_data_raw = { k: os.path.join(data_dir, v) for k, v in systems_data_raw_file.items() }

    systems_data = {}
    for system, data_path in systems_data_raw.items():
        try:
            with open(data_path, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Warning: File {data_path} not found. Skipping {system}.")
            systems_data[system] = {}
            continue

        # Initialize system data structure
        system_data = {}

        # Find all benchmark blocks
        if system == "RadixVM":
            blocks = re.split(r'echo Finish', content)
            for i in range(1, len(blocks)):
                block = blocks[i]
                # Extract thread count and finish time
                lines = block.split('\n')
                for line in lines:
                    match = re.search(r'^(\d+),\s*(\d+)', line)
                    
                    if match:
                        thread_count = int(match.group(1))
                        finish_time = int(match.group(2))
                        tput = finish_time_to_tput(finish_time)
                        
                        # Store the finish time for this thread count
                        if thread_count in system_data:
                            print("Thread count already exists for", system, ":", thread_count, ", picking the better one")
                            system_data[thread_count] = max(system_data[thread_count], tput)
                        else:
                            system_data[thread_count] = tput
        else:
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
                        # Extract thread count and finish time
                        lines = block_data.split('\n')
                        if lines:
                            match = re.search(r'(\d+),\s*(\d+)', lines[0])
                            
                            if match:
                                thread_count = int(match.group(1))
                                finish_time = int(match.group(2))
                                
                                # Store the finish time for this thread count
                                system_data[thread_count] = finish_time_to_tput(finish_time)
        
        systems_data[system] = system_data

    return systems_data
