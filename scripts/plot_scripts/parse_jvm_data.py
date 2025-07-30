from common import SYS_ADV, SYS_RW, SYS_BASE, SYS_DVA

import os
import re

def lat_ns_to_ms(lat):
    """
    Convert latency from nanoseconds to milliseconds.
    """
    return lat / 1_000_000

def parse_input():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    data_dir = os.path.join(script_dir, "../data/macro/jvm/")
    systems_data_raw_file = {
        SYS_ADV: "aster-rcu.txt",
        SYS_RW: "aster-rwlock.txt",
        "Linux": "linux-6.13.8.txt",
        "RadixVM": "well we didn't run",
        "NrOS": "well we didn't run",
        SYS_DVA: "dva.txt",
        SYS_BASE: "base.txt",
    }
    systems_data_raw = {k: os.path.join(data_dir, v) for k, v in systems_data_raw_file.items()}

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

        # Find all test blocks with thread counts and latencies
        # Pattern to match: "Using X threads" followed by TEST_START...TEST_END block
        pattern = r'\*\*\*TEST_START\*\*\*[\s\S]*?Using (\d+) threads[\s\S]*?Time consumed:\s*(\d+)\s*ns[\s\S]*?\*\*\*TEST_END\*\*\*'
        
        matches = re.finditer(pattern, content)
        
        for match in matches:
            thread_count = int(match.group(1))
            latency = lat_ns_to_ms(float(match.group(2)))

            if thread_count not in system_data:
                system_data[thread_count] = [latency]
            else:
                system_data[thread_count].append(latency)
        
        systems_data[system] = system_data

    # Calculate avg latencies for each thread count
    for system, data in systems_data.items():
        for thread_count, latencies in data.items():
            data[thread_count] = sum(latencies) / len(latencies)

    return systems_data
