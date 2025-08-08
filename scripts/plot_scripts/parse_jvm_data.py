from common import SYS_ADV, SYS_RW, SYS_BASE, SYS_DVA, find_and_read_latest_experiment_output, LINUX

import os
import re

def lat_ns_to_ms(lat):
    """
    Convert latency from nanoseconds to milliseconds.
    """
    return lat / 1_000_000

def parse_input():
    systems_data_raw = {
        SYS_ADV: find_and_read_latest_experiment_output("macrojvm", "corten-adv"),
        SYS_RW: find_and_read_latest_experiment_output("macrojvm", "corten-rw"),
        LINUX: find_and_read_latest_experiment_output("macrojvm", "linux"),
        SYS_DVA: find_and_read_latest_experiment_output("macrojvm", "corten-adv-dva"),
        SYS_BASE: find_and_read_latest_experiment_output("macrojvm", "corten-base"),
    }

    systems_data = {}
    for system, content in systems_data_raw.items():
        # Initialize system data structure
        system_data = {}

        if content is None:
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
