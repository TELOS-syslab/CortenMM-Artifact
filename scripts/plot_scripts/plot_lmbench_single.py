from common import common_plt_setting, common_ax_setting, get_presets, SYS_ADV, SYS_RW, styled_bar
from parse_parsec_data import parse_input as parse_parsec_input

import matplotlib.pyplot as plt
import os

def plot(axs):
    presets = get_presets()

    common_ax_setting(axs)

    benchmarks = {
        "fork": {
            SYS_ADV: 215.9231,
            SYS_RW: 223.8800,
            "Linux": 183.4483
        },
        "fork+exec": {
            SYS_ADV: 472.9167,
            SYS_RW: 496.5455,
            "Linux": 613.8750
        },
        "shell": {
            SYS_ADV: 714.7500,
            SYS_RW: 751.4286,
            "Linux": 733.3750
        }
    }

    systems = [SYS_ADV, SYS_RW, "Linux"]

    x = range(len(benchmarks))  # x positions for benchmarks, exlude dedup
    width = 0.15  # width of each bar
    clearance = 0.05  # clearance between bars
    num_systems = 3

    for i, sys_name in enumerate(systems):
        preset = presets[i]
        color = preset['color']
        hatch = preset['hatch']

        # Offset each system's bars to avoid overlap
        x_offset = [pos + i * (width + clearance) for pos in x]
        lats = []

        for bench_name, bench_data in benchmarks.items():
            lats.append(bench_data[sys_name])
        
        styled_bar(axs.bar, x_offset, lats, color, hatch, sys_name != SYS_ADV and sys_name != SYS_RW, width=width, label=sys_name)


    # Adjust x ticks to be in the middle of the grouped bars
    axs.set_xticks([pos + (num_systems - 1) * (width + clearance) / 2 for pos in x])
    # Adjust x ticks to be in the middle of the grouped bars
    axs.set_xticks([pos + (num_systems - 1) * (width + clearance) / 2 for pos in x])
    xlabels = [k for k in benchmarks.keys()]
    axs.set_xticklabels(xlabels, rotation=0, ha='center', fontsize=6)
    axs.set_ylabel("Latency (ms)", fontsize=8)
    axs.yaxis.set_major_locator(plt.MaxNLocator(6, min_n_ticks=4))
    axs.tick_params(axis='y', labelsize=6, pad=2)

    axs.legend(ncols=1, loc='upper left', fontsize=6, bbox_to_anchor=(0, 1.15))


def main():
    common_plt_setting()

    # Set up the plot
    # A4 paper is 8.27 x 11.69 inches
    # Set up the plot
    # A4 paper is 8.27 x 11.69 inches
    _, axs = plt.subplots(1, 1, figsize=(1.8, 1.2), dpi=400)

    plot(axs)

    # Save the figure as a file and show the plot
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    plt.savefig(os.path.join(parent_dir, "lmbench-proc.pdf"), bbox_inches='tight')

if __name__ == '__main__':
    main()