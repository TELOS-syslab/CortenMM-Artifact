from common import SYS_ADV, SYS_RW, find_latest_experiment_output

import os
import re
import json

# NROS uses a different output format
def nros_input():
    print("WARNING: NROS script not implemented yet, using dummy data")
    return { "map": {}, "unmap": {} }

def parse_input():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    data_dir = os.path.join(script_dir, "../data/micro/")
    systems_data_raw = {
        SYS_ADV: find_latest_experiment_output("microbench", "corten-adv"),
        SYS_RW: find_latest_experiment_output("microbench", "corten-rw"),
        "Linux": find_latest_experiment_output("microbench", "linux"),
        "RadixVM": find_latest_experiment_output("microbench", "radixvm")
    }

    systems_data = {}
    for system, data_path in systems_data_raw.items():
        if data_path is None:
            print(f"Warning: No data file found for {system}. Skipping.")
            continue

        with open(data_path, 'r') as f:
            content = f.read()

        # Initialize system data structure
        system_data = {}

        # Find all benchmark blocks
        blocks = re.split(r'\*\*\*(.*?)\*\*\*', content)
        # Skip first element (content before first benchmark)
        blocks = blocks[1:]

        # Process in pairs (name, data)
        for i in range(0, len(blocks), 2):
            if i + 1 < len(blocks):
                benchmark_name = blocks[i].strip()
                benchmark_data = blocks[i+1].strip()
                
                # Extract thread count and latency data
                thread_match = re.search(r'<#\)<\+< RESULTS of (\d+) threads >\+>\(#>', benchmark_data)
                lat_match = re.search(r'Avg Lat \(ns\): ([\d\s]+)', benchmark_data)
                
                if thread_match and lat_match:
                    thread_count = int(thread_match.group(1))
                    lat_values = [int(x) for x in lat_match.group(1).strip().split()]
                    
                    # Initialize benchmark data if not exists
                    if benchmark_name not in system_data:
                        system_data[benchmark_name] = {}
                    
                    # TODO: Adjust all TSC frequencies to 2.25 GHz. Some of them uses 1.9 GHz still
                    if system == "Linux":
                        lat_values = [x * 190 / 225 for x in lat_values]

                    # Store the latency values for this thread count
                    system_data[benchmark_name][thread_count] = lat_values
        
        systems_data[system] = system_data

    # Add NROS data
    nros_data = nros_input()
    systems_data["NrOS"] = nros_data

    return systems_data
