from microdata import parse_input
from common import common_plt_setting, get_presets, common_ax_setting, SYS_ADV, SYS_RW, SYS

import os
import matplotlib.pyplot as plt

def avg_lat_to_tput(lat, nthreads):
    """
    Convert average latency to throughput.
    :param lat: Average latency in nanoseconds.
    :param nthreads: Number of threads.
    :return: Throughput in operations per microseconds.
    """
    return 1e3 / lat * nthreads

def plot_scale(ax, preset, sys_name, data, plot_xtick=False):
    tputs = [avg_lat_to_tput(sum(l[-16:]) / len(l[-16:]), t) for t, l in data.items()]
    xticks = list(data.keys())
    x = list(range(len(xticks)))

    color = preset['color']
    fmt = preset['marker']
    linestyle = preset['linestyle']
    
    ax.plot(x, tputs, label=sys_name, color=color, markersize=3, marker=fmt, alpha=1, linestyle=linestyle)

    if plot_xtick:
        ax.set_xticks(x)
        ax.set_xticklabels(xticks, fontsize=6)
        ax.tick_params(axis='x', rotation=90, pad=2)
    
    # Set y tick font size and increase pad
    ax.tick_params(axis='y', labelsize=6, pad=2)
    ax.yaxis.offsetText.set_fontsize(8)
    ax.yaxis.set_major_locator(plt.MaxNLocator(5, integer=True, min_n_ticks=4))

def main():
    data = parse_input()

    common_plt_setting()
    presets = get_presets()

    # Plot throughput of in a 5 cols 3 rows grid
    # A4 paper is 8.27 x 11.69 inches
    fig, axs = plt.subplots(1, 2, figsize=(4, 0.8), dpi=400)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.98, bottom=0.02, wspace=0.15, hspace=0.20)

    for ax in axs.flat:
        common_ax_setting(ax)

    axs[0].set_ylabel('Throughput\\\\\n(ops/$\\mu$s)', fontsize=8)

    axs[0].set_title(r'(a) \texttt{mmap}-PF', fontsize=8)
    axs[1].set_title(r'(b) \texttt{munmap}', fontsize=8)

    axs[0].set_xlabel(r'\#threads', fontsize=8)
    axs[1].set_xlabel(r'\#threads', fontsize=8)

    # plot x ticks only for the first time.
    first_print = True

    for i, (sys_name, bench_data) in enumerate(data.items()):
        preset = presets[i]

        label = sys_name
        if sys_name == SYS_RW:
            continue
        elif sys_name == SYS_ADV:
            label = SYS
        elif sys_name == 'Linux':
            label = "Linux-6.13.8"

        if "MMAP_PF UNFIXED" in bench_data:
            plot_scale(axs[0], preset, label, bench_data["MMAP_PF UNFIXED"], first_print)

        if "MUNMAP_VIRT LOW_CONTENTION" in bench_data:
            plot_scale(axs[1], preset, label, bench_data["MUNMAP_VIRT LOW_CONTENTION"], first_print)

        if sys_name == "NrOS":
            # plot_scale(axs[0], preset, sys_name, bench_data["map"])
            pass
        
        first_print = False
    
    # clear x ticks for the first row
    # for ax in axs[0, :]:
    #     ax.set_xticklabels([])

    # Get all handles and labels from the first plot
    handles, labels = axs[1].get_legend_handles_labels()
    
    # Show first 2 systems in the first figure
    axs[0].legend(handles[:2], labels[:2], loc='upper left', ncol=1, fontsize=6)
    
    # Show the rest of the systems in the second figure
    if len(handles) > 2:
        axs[1].legend(handles[2:], labels[2:], loc='upper left', ncol=1, fontsize=6)

    # Save the plot as PDF
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    plt.savefig(parent_dir + "/intro-two-micro.pdf", bbox_inches='tight')


if __name__ == "__main__":
    main()
