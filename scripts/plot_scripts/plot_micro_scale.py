from microdata import parse_input
from common import common_plt_setting, get_presets, common_ax_setting, SYS_ADV, SYS_RW

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
    fig, axs = plt.subplots(2, 5, figsize=(8, 2), dpi=400)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.83, bottom=0.12, wspace=0.15, hspace=0.20)

    fig.supylabel(r'Throughput (ops/$\mu$s)', fontsize=8)

    for ax in axs.flat:
        common_ax_setting(ax)

    axs[0, 0].set_title(r'\texttt{mmap}', fontsize=8)
    axs[0, 1].set_title(r'\texttt{mmap}-PF', fontsize=8)
    axs[0, 2].set_title('PF', fontsize=8)
    axs[0, 3].set_title(r'\texttt{unmap}-virt', fontsize=8)
    axs[0, 4].set_title(r'\texttt{unmap}', fontsize=8)

    axs[1, 0].set_xlabel(r'\#threads', fontsize=8)
    axs[1, 1].set_xlabel(r'\#threads', fontsize=8)
    axs[1, 2].set_xlabel(r'\#threads', fontsize=8)
    axs[1, 3].set_xlabel(r'\#threads', fontsize=8)
    axs[1, 4].set_xlabel(r'\#threads', fontsize=8)

    axs[0, 0].set_ylabel('Low Contention', fontsize=8, labelpad=6)
    axs[1, 0].set_ylabel('High Contention', fontsize=8, labelpad=6)

    # plot x ticks only for the first time.
    first_print = True

    for i, (sys_name, bench_data) in enumerate(data.items()):
        preset = presets[i]

        if "MMAP UNFIXED" in bench_data:
            plot_scale(axs[0, 0], preset, sys_name, bench_data["MMAP UNFIXED"], first_print)
        if "MMAP FIXED HIGH_CONTENTION" in bench_data:
            plot_scale(axs[1, 0], preset, sys_name, bench_data["MMAP FIXED HIGH_CONTENTION"], first_print)

        if "MMAP_PF UNFIXED" in bench_data:
            plot_scale(axs[0, 1], preset, sys_name, bench_data["MMAP_PF UNFIXED"], first_print)
        if "MMAP_PF FIXED HIGH_CONTENTION" in bench_data:
            plot_scale(axs[1, 1], preset, sys_name, bench_data["MMAP_PF FIXED HIGH_CONTENTION"], first_print)

        if "PF LOW_CONTENTION" in bench_data:
            plot_scale(axs[0, 2], preset, sys_name, bench_data["PF LOW_CONTENTION"], first_print)
        if "PF HIGH_CONTENTION" in bench_data:
            plot_scale(axs[1, 2], preset, sys_name, bench_data["PF HIGH_CONTENTION"], first_print)

        if "MUNMAP_VIRT LOW_CONTENTION" in bench_data:
            plot_scale(axs[0, 3], preset, sys_name, bench_data["MUNMAP_VIRT LOW_CONTENTION"], first_print)
        if "MUNMAP_VIRT HIGH_CONTENTION" in bench_data:
            plot_scale(axs[1, 3], preset, sys_name, bench_data["MUNMAP_VIRT HIGH_CONTENTION"], first_print)

        if "MUNMAP LOW_CONTENTION" in bench_data:
            plot_scale(axs[0, 4], preset, sys_name, bench_data["MUNMAP LOW_CONTENTION"], first_print)
        if "MUNMAP HIGH_CONTENTION" in bench_data:
            plot_scale(axs[1, 4], preset, sys_name, bench_data["MUNMAP HIGH_CONTENTION"], first_print)

        if sys_name == "NrOS":
            plot_scale(axs[0, 1], preset, sys_name, bench_data["map"])
            plot_scale(axs[1, 1], preset, sys_name, bench_data["map"])
            plot_scale(axs[0, 4], preset, sys_name, bench_data["unmap"])
        
        first_print = False
    
    # clear x ticks for the first row
    for ax in axs[0, :]:
        ax.set_xticklabels([])

    # Get all handles and labels from the first plot
    handles, labels = axs[0, 1].get_legend_handles_labels()
    
    # Show first 2 systems in the first figure
    axs[0, 0].legend(handles[:2], labels[:2], loc='upper left', ncol=1, fontsize=6)
    
    # Show the rest of the systems in the second figure
    if len(handles) > 2:
        axs[0, 1].legend(handles[2:], labels[2:], loc='upper left', ncol=1, fontsize=6)

    
    # Calculate performance differences compared to Linux
    benchmarks = {
        "MMAP UNFIXED": axs[0, 0],
        "MMAP_PF UNFIXED": axs[0, 1],
        "PF LOW_CONTENTION": axs[0, 2],
        "MUNMAP_VIRT LOW_CONTENTION": axs[0, 3],
        "MUNMAP LOW_CONTENTION": axs[0, 4],
        "MMAP FIXED HIGH_CONTENTION": axs[1, 0],
        "MMAP_PF FIXED HIGH_CONTENTION": axs[1, 1],
        "PF HIGH_CONTENTION": axs[1, 2],
        "MUNMAP_VIRT HIGH_CONTENTION": axs[1, 3],
        "MUNMAP HIGH_CONTENTION": axs[1, 4],
    }
    for benchmark in benchmarks.keys():
        if benchmark not in data["Linux"] or benchmark not in data[SYS_ADV] or benchmark not in data[SYS_RW]:
            continue
        for c in [64, 384]:
            linux_lat = sum(data["Linux"][benchmark][c][-16:]) / 16
            linux_tput = avg_lat_to_tput(linux_lat, c)
            
            adv_lat = sum(data[SYS_ADV][benchmark][c][-16:]) / 16
            adv_tput = avg_lat_to_tput(adv_lat, c)
            adv_diff = ((adv_tput - linux_tput) / linux_tput) * 100
            
            rw_lat = sum(data[SYS_RW][benchmark][c][-16:]) / 16
            rw_tput = avg_lat_to_tput(rw_lat, c)
            rw_diff = ((rw_tput - linux_tput) / linux_tput) * 100
            
            # Terminal output
            print(f"{benchmark}: {SYS_ADV} outperforms Linux by {adv_diff:.2f}% at {c}")
            print(f"{benchmark}: {SYS_RW} outperforms Linux by {rw_diff:.2f}% at {c}")

    # Save the plot as PDF
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    plt.savefig(parent_dir + "/micro-scale-tput.pdf", bbox_inches='tight')


if __name__ == "__main__":
    main()
