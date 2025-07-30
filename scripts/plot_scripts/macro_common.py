from common import common_ax_setting, get_presets, SYS_ADV, SYS_RW

import matplotlib.pyplot as plt

def plot(axs, data, xtick=False):
    presets = get_presets()

    common_ax_setting(axs)

    for i, (sys_name, bench_data) in enumerate(data.items()):
        preset = presets[i]

        if len(bench_data) == 0:
            print(f"Warning: No data for {sys_name}. Skipping.")
            continue

        tputs = list(bench_data.values())
        xticks = list(bench_data.keys())
        x = list(range(len(xticks)))

        color = preset['color']
        fmt = preset['marker']
        linestyle = preset['linestyle']
        
        axs.plot(x, tputs, label=sys_name, color=color, markersize=3, marker=fmt, alpha=1, linestyle=linestyle)

    # Set tick parameters on the axes object
    xticks = list(list(data.values())[0].keys())
    x = list(range(len(xticks)))
    if xtick:
        axs.set_xticks(x)
        axs.set_xticklabels(xticks, rotation=90, fontsize=6)
    else:
        axs.set_xticks(x)
        axs.set_xticklabels([])

    axs.tick_params(axis='y', labelsize=6)

    # don't plot y < 0
    axs.set_ylim(bottom=0)
    axs.yaxis.set_major_locator(plt.MaxNLocator(5, integer=True, min_n_ticks=4))
