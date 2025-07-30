from common import SYS_ADV, SYS_RW

import os
import re
import json

# NROS uses a different json format
def nros_input():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "../data/micro/")
    nros_json = os.path.join(data_dir, "nros.json")
    
    data = json.load(open(nros_json, 'r'))

    # change the type of keys from string to int
    keys = list(data["map"].keys())
    for key in keys:
        data["map"][int(key)] = data["map"].pop(key)

    keys = list(data["unmap"].keys())
    for key in keys:
        data["unmap"][int(key)] = data["unmap"].pop(key)

    data["map"][128] = data["map"].pop(127)

    data["unmap"][4] = data["unmap"].pop(3)

    return data

def parse_input():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    data_dir = os.path.join(script_dir, "../data/micro/")
    systems_data_raw_file = {
        SYS_ADV: "aster-rcu.txt",
        SYS_RW: "aster-rwl.txt",
        "Linux": "linux-6.13.8.txt",
        "RadixVM": "radixvm.txt"
    }
    systems_data_raw = { k: os.path.join(data_dir, v) for k, v in systems_data_raw_file.items() }

    systems_data = {}
    for system, data_path in systems_data_raw.items():
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

                    # Store the latency values for this thread count
                    system_data[benchmark_name][thread_count] = lat_values
        
        systems_data[system] = system_data

    # Add NROS data
    nros_data = nros_input()
    systems_data["NrOS"] = nros_data

    return systems_data
