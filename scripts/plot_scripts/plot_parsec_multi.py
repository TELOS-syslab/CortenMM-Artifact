from common import common_plt_setting, common_ax_setting, get_presets, SYS_ADV, SYS_RW, styled_bar
from parse_parsec_data import parse_input as parse_parsec_input

import matplotlib.pyplot as plt
import os

def plot(axs):
    presets = get_presets()

    common_ax_setting(axs)

    benchmarks = parse_parsec_input()
    filtered = ['dedup']

    systems = [SYS_ADV, SYS_RW, "Linux"]

    x = range(len(benchmarks) - len(filtered))  # x positions for benchmarks, exlude dedup
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
            if bench_name in filtered:
                continue # Already evaluated

            if sys_name in bench_data and 8 in bench_data[sys_name]:
                # this is tput
                tput = bench_data[sys_name][8]
                ratio = tput / benchmarks[bench_name]["Linux"][8]
                ratios.append(ratio)
            else:
                ratios.append(0)
        
        styled_bar(axs.bar, x_offset, ratios, color, hatch, sys_name != SYS_ADV and sys_name != SYS_RW, width=width, label=sys_name)


    # Adjust x ticks to be in the middle of the grouped bars
    axs.set_xticks([pos + (num_systems - 1) * (width + clearance) / 2 for pos in x])
    # Adjust x ticks to be in the middle of the grouped bars
    axs.set_xticks([pos + (num_systems - 1) * (width + clearance) / 2 for pos in x])
    xlabels = [k for k in benchmarks.keys() if k not in filtered]
    axs.set_xticklabels(xlabels, rotation=30, ha='right', fontsize=6)
    axs.set_ylabel("Throughput Ratio", fontsize=8)
    axs.yaxis.set_ticks([0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4])
    # axs.yaxis.set_major_locator(plt.MaxNLocator(6, integer=True, min_n_ticks=4))
    axs.tick_params(axis='y', labelsize=6, pad=2)

    axs.legend(ncols=1, loc='upper right', fontsize=6, bbox_to_anchor=(1, 1.15))


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
    plt.savefig(os.path.join(parent_dir, "macro-multi-tput.pdf"), bbox_inches='tight')

if __name__ == '__main__':
    main()