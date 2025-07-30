from common import common_plt_setting, common_ax_setting, get_presets, SYS_ADV, SYS_RW, SYS_ADV_TC, LINUX_TC, SYS_RW_TC, LINUX_PT, SYS_ADV_PT, SYS_RW_PT, LINUX
from macro_common import plot
from parse_metis_data import parse_input as parse_metis_input
from parse_dedup_data import parse_input as parse_dedup_input
from parse_psearchy_data import parse_input as parse_psearchy_input

from parse_jvm_data import parse_input as parse_jvm_input

from aster_breakdowndata import parse_breakdowns as parse_aster_breakdowns
from breakdown import plot_linux_perf_breakdown, plot_breakdown

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from matplotlib.gridspec import GridSpec

def main():
    common_plt_setting()

    # Set up the plot
    # A4 paper is 8.27 x 11.69 inches
    fig = plt.figure(figsize=(4, 2.6), dpi=400)
    gs = GridSpec(8, 3, width_ratios=[1.5, 1, 1])

    # Create a dict for the axes
    axs = {}

    # First two (split)

    # First column (no split)
    axs[2, 0, 0] = fig.add_subplot(gs[0:2, 0])
    axs[3, 0, 0] = fig.add_subplot(gs[2:4, 0])

    # Column 1 and 2 (split rows 0 and 1)
    axs[2, 1, 0] = fig.add_subplot(gs[0, 1])  # top
    axs[2, 2, 0] = fig.add_subplot(gs[0, 2])  # top
    axs[3, 1, 0] = fig.add_subplot(gs[2, 1])  # top
    axs[3, 2, 0] = fig.add_subplot(gs[2, 2])  # top

    # Bottom parts of the split rows
    axs[2, 1, 1] = fig.add_subplot(gs[1, 1])  # bottom of axs[0, 1]
    axs[2, 2, 1] = fig.add_subplot(gs[1, 2])  # bottom of axs[0, 2]
    axs[3, 1, 1] = fig.add_subplot(gs[3, 1])  # bottom of axs[1, 1]
    axs[3, 2, 1] = fig.add_subplot(gs[3, 2])  # bottom of axs[1, 2]

    plot(axs[0, 0, 0], parse_dedup_input())
    plot_linux_perf_breakdown(axs[0, 1, 0], "dedup")
    plot_linux_perf_breakdown(axs[0, 1, 1], "dedup-tc")
    aster_breakdown = parse_aster_breakdowns("dedup")
    plot_breakdown(axs[0, 2, 0], aster_breakdown, yticklabel=True)
    aster_breakdown_tc = parse_aster_breakdowns("dedup-tc")
    plot_breakdown(axs[0, 2, 1], aster_breakdown_tc, yticklabel=True)

    plot(axs[1, 0, 0], parse_psearchy_input(), xtick=True)
    plot_linux_perf_breakdown(axs[1, 1, 0], "psearchy")
    plot_linux_perf_breakdown(axs[1, 1, 1], "psearchy-tc", xticklabel=True)
    aster_breakdown = parse_aster_breakdowns("psearchy")
    plot_breakdown(axs[1, 2, 0], aster_breakdown, yticklabel=True)
    aster_breakdown_tc = parse_aster_breakdowns("psearchy-tc")
    plot_breakdown(axs[1, 2, 1], aster_breakdown_tc, yticklabel=True)

    # Get all handles and labels from the first tput
    handles, labels = axs[0, 0, 0].get_legend_handles_labels()
    axs[0, 0, 0].legend(handles[:2], labels[:2], loc='upper left', ncol=1, fontsize=6)
    axs[1, 0, 0].legend(handles[2:], labels[2:], loc='upper left', ncol=1, fontsize=6)

    # Get all handles and labels from the first breakdown
    # handles, labels = axs[0, 1, 0].get_legend_handles_labels()
    # axs[0, 1, 0].legend(handles[:2], labels[:2], loc='lower left', bbox_to_anchor=(-0.05, 0), ncol=1, fontsize=6)
    # axs[0, 1, 1].legend(handles[2:4], labels[2:4], loc='lower left', bbox_to_anchor=(-0.05, 0), ncol=1, fontsize=6)
    # axs[1, 1, 0].legend(handles[4:], labels[4:], loc='lower left', bbox_to_anchor=(-0.05, 0), ncol=1, fontsize=6)

    # Get all handles and labels from the first breakdown
    handles, labels = axs[0, 2, 0].get_legend_handles_labels()
    axs[0, 2, 0].legend(handles[:2], labels[:2], loc='lower left', bbox_to_anchor=(-0.05, 0), ncol=1, fontsize=6)
    axs[0, 2, 1].legend(handles[2:4], labels[2:4], loc='lower left', bbox_to_anchor=(-0.05, 0), ncol=1, fontsize=6)
    axs[1, 2, 0].legend(handles[4:], labels[4:], loc='lower left', bbox_to_anchor=(-0.05, 0), ncol=1, fontsize=6)

    axs[0, 1, 0].set_title(f'{LINUX}', fontsize=8)
    axs[0, 2, 0].set_title(f'{SYS_ADV}', fontsize=8)

    axs[0, 2, 0].yaxis.set_label_position("right")
    axs[0, 2, 0].set_ylabel(r'\texttt{ptmalloc}', fontsize=8)
    axs[0, 2, 1].yaxis.set_label_position("right")
    axs[0, 2, 1].set_ylabel(r'\texttt{tcmalloc}', fontsize=8)
    axs[1, 2, 0].yaxis.set_label_position("right")
    axs[1, 2, 0].set_ylabel(r'\texttt{ptmalloc}', fontsize=8)
    axs[1, 2, 1].yaxis.set_label_position("right")
    axs[1, 2, 1].set_ylabel(r'\texttt{tcmalloc}', fontsize=8)

    axs[1, 0, 0].set_xlabel(r'\#threads', fontsize=8)
    axs[1, 1, 1].set_xlabel(r'\#threads', fontsize=8)
    axs[1, 2, 1].set_xlabel(r'\#threads', fontsize=8)

    axs[0, 0, 0].set_ylabel('\\texttt{dedup}\n\nThroughput\n(jobs/min)', fontsize=8)

    axs[1, 0, 0].set_ylabel('\\texttt{psearchy}\n\nThroughput\n(jobs/min)', fontsize=8)

    # Print the gains of SYS_ADV and SYS_RW over Linux on every benchmark
    benches = {
        "dedup": parse_dedup_input(),
        "psearchy": parse_psearchy_input()
    }
    for bench_name, data in benches.items():
        for c in [64, 128, 384]:
            linux_tput = data[LINUX_PT][c]
            sys_adv_tput = data[SYS_ADV_PT][c]
            sys_rw_tput = data[SYS_RW_PT][c]

            # Calculate the gains
            adv_gain = (sys_adv_tput - linux_tput) / linux_tput * 100
            rw_gain = (sys_rw_tput - linux_tput) / linux_tput * 100

            print(f"[{c}] {bench_name}: SYS_ADV gain: {adv_gain:.2f}%, SYS_RW gain: {rw_gain:.2f}%")

    # Save the figure as a file and show the plot
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    plt.subplots_adjust(left=0.18, right=0.95, top=0.99, bottom=0.2, hspace=0.15, wspace=0.05)
    plt.savefig(os.path.join(parent_dir, "macro-tput-tc.pdf"), bbox_inches='tight')

if __name__ == '__main__':
    main()