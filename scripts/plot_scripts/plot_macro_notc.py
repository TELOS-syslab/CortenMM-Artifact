from common import common_plt_setting, common_ax_setting, get_presets, SYS_ADV, SYS_RW
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

def main():
    common_plt_setting()

    # Set up the plot
    # A4 paper is 8.27 x 11.69 inches
    fig, axs = plt.subplots(2, 3, figsize=(4, 2), dpi=400, gridspec_kw={'width_ratios': [1.5, 1, 1]})

    plot(axs[0, 0], parse_jvm_input())
    plot_linux_perf_breakdown(axs[0, 1], "jvm")
    aster_breakdown = parse_aster_breakdowns("jvm")
    plot_breakdown(axs[0, 2], aster_breakdown, yticklabel=True)

    plot(axs[1, 0], parse_metis_input(), xtick=True)
    plot_linux_perf_breakdown(axs[1, 1], "metis", xticklabel=True)
    aster_breakdown = parse_aster_breakdowns("metis")
    plot_breakdown(axs[1, 2], aster_breakdown, yticklabel=True, xticklabel=True)

    # Get all handles and labels from the second tput
    handles, labels = axs[1, 0].get_legend_handles_labels()
    axs[0, 0].legend(handles[:2] + handles[4:], labels[:2] + labels[4:], loc='upper left', ncol=1, fontsize=6)
    axs[1, 0].legend(handles[2:4], labels[2:4], loc='upper left', ncol=1, fontsize=6)

    # Get all handles and labels from the first breakdown
    handles, labels = axs[0, 1].get_legend_handles_labels()
    axs[0, 1].legend(handles[:2], labels[:2], loc='lower left', bbox_to_anchor=(-0.05, 0), ncol=1, fontsize=6)
    axs[0, 2].legend(handles[2:4], labels[2:4], loc='lower left', bbox_to_anchor=(-0.05, 0), ncol=1, fontsize=6)
    axs[1, 2].legend(handles[4:], labels[4:], loc='lower left', bbox_to_anchor=(-0.05, 0), ncol=1, fontsize=6)

    axs[0, 1].set_title('Linux', fontsize=8)
    axs[0, 2].set_title(f'{SYS_ADV}', fontsize=8)

    axs[1, 0].set_xlabel(r'\#threads', fontsize=8)
    axs[1, 1].set_xlabel(r'\#threads', fontsize=8)
    axs[1, 2].set_xlabel(r'\#threads', fontsize=8)

    axs[0, 0].set_ylabel('JVM Thread\n\nLatency\n(ms)', fontsize=8)

    axs[1, 0].set_ylabel('\\texttt{metis}\n\nThroughput\n(jobs/min)', fontsize=8)

    # Print the gains of SYS_ADV and SYS_RW over Linux on every benchmark
    benches = {
        "jvm": parse_jvm_input(),
        "metis": parse_metis_input(),
    }
    for bench_name, data in benches.items():
        for c in [64, 128, 384]:
            linux_tput = data["Linux"][c]
            sys_adv_tput = data[SYS_ADV][c]
            sys_rw_tput = data[SYS_RW][c]

            # Calculate the gains
            adv_gain = (sys_adv_tput - linux_tput) / linux_tput * 100
            rw_gain = (sys_rw_tput - linux_tput) / linux_tput * 100

            print(f"[{c}] {bench_name}: SYS_ADV gain: {adv_gain:.2f}%, SYS_RW gain: {rw_gain:.2f}%")

            if "RadixVM" in data:
                if c in data['RadixVM']:
                    radixvm_tput = data['RadixVM'][c]
                    adv_gain = (sys_adv_tput - radixvm_tput) / radixvm_tput * 100
                    rw_gain = (sys_rw_tput - radixvm_tput) / radixvm_tput * 100
                    print(f"[{c}] {bench_name}: SYS_ADV gain: {adv_gain:.2f}%, SYS_RW gain: {rw_gain:.2f}% over Radix")

    # Save the figure as a file and show the plot
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    plt.subplots_adjust(left=0.18, right=0.95, top=0.99, bottom=0.2, hspace=0.1, wspace=0.05)
    plt.savefig(os.path.join(parent_dir, "macro-tput-notc.pdf"), bbox_inches='tight')

if __name__ == '__main__':
    main()