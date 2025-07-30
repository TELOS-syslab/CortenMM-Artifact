from microdata import parse_input
from common import common_plt_setting, get_presets, common_ax_setting, styled_bar, SYS_ADV, SYS_RW

import os
import matplotlib.pyplot as plt

def avg_lat_to_tput(lat):
    """
    Convert average latency to throughput.
    :param lat: Average latency in nanoseconds.
    :return: Throughput in operations per microseconds.
    """
    return 1e3 / lat

def main():
    data = parse_input()

    common_plt_setting()
    presets = get_presets()

    # Plot throughput within a bar chart in a single column
    # A4 paper is 8.27 x 11.69 inches
    fig, axs = plt.subplots(1, 1, figsize=(4, 1), dpi=400)
    benchmarks = {
        "MMAP UNFIXED": r"\texttt{mmap}",
        "MMAP_PF UNFIXED" : r"\texttt{mmap}-PF",
        "PF LOW_CONTENTION": r"PF",
        "MUNMAP_VIRT LOW_CONTENTION": r"\texttt{unmap}-virt",
        "MUNMAP LOW_CONTENTION": r"\texttt{unmap}",
    }

    common_ax_setting(axs)

    x = range(len(benchmarks))  # x positions for benchmarks
    width = 0.1  # width of each bar
    clearance = 0.05  # clearance between bars
    num_systems = len(data)

    for i, (sys_name, bench_data) in enumerate(data.items()):
        preset = presets[i]
        color = preset['color']
        hatch = preset['hatch']

        # Offset each system's bars to avoid overlap
        x_offset = [pos + i * (width + clearance) for pos in x]

        tputs = []

        if sys_name  == "NrOS":
            tputs.append(0) # mmap
            tputs.append(avg_lat_to_tput(sum(bench_data["map"][1][-16:]) / 16)) # mmap-pf
            tputs.append(0) # pf
            tputs.append(0) # munmap-virt
            tputs.append(avg_lat_to_tput(sum(bench_data["unmap"][1][-16:]) / 16)) # munmap
        else:
            for benchmark in benchmarks.keys():
                if benchmark in bench_data:
                    lat = sum(bench_data[benchmark][1][-16:]) / 16
                    tputs.append(avg_lat_to_tput(lat))
                else:
                    tputs.append(0)  # No data for this benchmark

        styled_bar(axs.bar, x_offset, tputs, color, hatch, sys_name != SYS_ADV and sys_name != SYS_RW, width=width, label=sys_name)

    # Adjust x ticks to be in the middle of the grouped bars
    axs.set_xticks([pos + (num_systems - 1) * (width + clearance) / 2 for pos in x])
    axs.set_xticklabels(benchmarks.values(), rotation=0, ha='center', fontsize=8)
    axs.set_ylabel("Throughput\n(ops/$\\mu$s)", fontsize=8)
    axs.yaxis.set_major_locator(plt.MaxNLocator(5, integer=True, min_n_ticks=4))
    axs.tick_params(axis='y', labelsize=6, pad=2)

    axs.legend(fontsize=6, ncol=2, loc="upper center", bbox_to_anchor=(0.6, 1.1), columnspacing=10)

    # Calculate performance differences compared to Linux
    diff_labels = []
    for benchmark in benchmarks.keys():
        if benchmark not in data["Linux"] or benchmark not in data[SYS_ADV] or benchmark not in data[SYS_RW]:
            diff_labels.append(("N/A", "N/A"))
            continue
            
        linux_lat = sum(data["Linux"][benchmark][1][-16:]) / 16
        linux_tput = avg_lat_to_tput(linux_lat)
        
        adv_lat = sum(data[SYS_ADV][benchmark][1][-16:]) / 16
        adv_tput = avg_lat_to_tput(adv_lat)
        adv_diff = ((adv_tput - linux_tput) / linux_tput) * 100
        
        rw_lat = sum(data[SYS_RW][benchmark][1][-16:]) / 16
        rw_tput = avg_lat_to_tput(rw_lat)
        rw_diff = ((rw_tput - linux_tput) / linux_tput) * 100
        
        diff_labels.append((f"{'+' if adv_diff >= 0 else ''}{adv_diff:.1f}\\%", 
                           f"{'+' if rw_diff >= 0 else ''}{rw_diff:.1f}\\%"))
        
        # Terminal output
        print(f"{benchmark}: {SYS_ADV} outperforms Linux by {adv_diff:.2f}%")
        print(f"{benchmark}: {SYS_RW} outperforms Linux by {rw_diff:.2f}%")
    
    # Add percentage labels under x-tick labels
    for i, pos in enumerate(x):
        x_center = pos + (num_systems - 1) * (width + clearance) / 2
        if diff_labels[i][0] != "N/A":
            axs.text(x_center, -0.5, f"{diff_labels[i][0]}\n{diff_labels[i][1]}", 
                    ha='center', va='top', fontsize=6)

    # Add row labels for SYS_ADV and SYS_RW
    axs.text(-1.2, -0.5, f"{SYS_ADV}:\n{SYS_RW}:", ha='left', va='top', fontsize=6)
            
    # Save the plot as PDF
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    plt.savefig(parent_dir + "/micro-single-tput.pdf", bbox_inches='tight')

if __name__ == "__main__":
    main()
