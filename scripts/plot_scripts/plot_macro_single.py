from common import common_plt_setting, common_ax_setting, get_presets, SYS_ADV, SYS_RW, styled_bar, LINUX_PT, SYS_ADV_PT, SYS_RW_PT, LINUX
from parse_metis_data import parse_input as parse_metis_input
from parse_dedup_data import parse_input as parse_dedup_input
from parse_psearchy_data import parse_input as parse_psearchy_input
from parse_parsec_data import parse_input as parse_parsec_input
from parse_jvm_data import parse_input as parse_jvm_input

import matplotlib.pyplot as plt
import os

def plot(axs):
    presets = get_presets()

    common_ax_setting(axs)

    benchmarks = {
        "Metis": parse_metis_input(),
        "Psearchy": parse_psearchy_input(),
        "JVM": parse_jvm_input(),
    }

    benchmarks.update(parse_parsec_input())

    systems = [
        SYS_ADV,
        SYS_RW,
        "Linux",
        "RadixVM",
    ]

    x = range(len(benchmarks))  # x positions for benchmarks
    width = 0.15  # width of each bar
    clearance = 0.05  # clearance between bars
    num_systems = 3

    for i, sys_name in enumerate(systems):
        preset = presets[i]
        color = preset['color']
        hatch = preset['hatch']

        # Offset each system's bars to avoid overlap
        x_offset = [pos + i * (width + clearance) for pos in x]
        ratios = []

        for bench_name, bench_data in benchmarks.items():
            linux_name = LINUX_PT
            if bench_name != "Psearchy":
                sys_name_corr = sys_name
                linux_name = LINUX
            elif sys_name == "Linux":
                sys_name_corr = LINUX_PT
            elif sys_name == SYS_ADV:
                sys_name_corr = SYS_ADV_PT
            elif sys_name == SYS_RW:
                sys_name_corr = SYS_RW_PT
            
            if bench_name == "JVM":
                # This is lat
                if sys_name_corr in bench_data and 1 in bench_data[sys_name_corr]:
                    lat = bench_data[sys_name_corr][1]
                    ratio = benchmarks[bench_name][linux_name][1] / lat
                    ratios.append(ratio)
                else:
                    ratios.append(0)
            else:
                # This is tput
                if sys_name_corr in bench_data and 1 in bench_data[sys_name_corr]:
                    tput = bench_data[sys_name_corr][1]
                    ratio = tput / benchmarks[bench_name][linux_name][1]
                    ratios.append(ratio)
                else:
                    ratios.append(0)
        
        styled_bar(axs.bar, x_offset, ratios, color, hatch, sys_name != SYS_ADV and sys_name != SYS_RW, width=width, label=sys_name)


    # Adjust x ticks to be in the middle of the grouped bars
    axs.set_xticks([pos + (num_systems - 1) * (width + clearance) / 2 for pos in x])
    # Adjust x ticks to be in the middle of the grouped bars
    axs.set_xticks([pos + (num_systems - 1) * (width + clearance) / 2 for pos in x])
    axs.set_xticklabels(benchmarks.keys(), rotation=20, ha='right', fontsize=6)
    axs.tick_params(axis='x', pad=1)
    axs.set_ylabel("Throughput Ratio", fontsize=8)
    axs.yaxis.set_major_locator(plt.MaxNLocator(7, integer=True, min_n_ticks=6))
    axs.tick_params(axis='y', labelsize=6, pad=2)

    axs.legend(ncols=4, loc='upper center', fontsize=6, bbox_to_anchor=(0.5, 1.3))


def main():
    common_plt_setting()

    # Set up the plot
    # A4 paper is 8.27 x 11.69 inches
    # Set up the plot
    # A4 paper is 8.27 x 11.69 inches
    _, axs = plt.subplots(1, 1, figsize=(4, 0.8), dpi=400)

    plot(axs)

    # Save the figure as a file and show the plot
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    plt.savefig(os.path.join(parent_dir, "macro-single-tput.pdf"), bbox_inches='tight')

if __name__ == '__main__':
    main()