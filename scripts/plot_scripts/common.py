# Common functions for plotting

# System names

SYS = r"\textsc{CortenMM}"
SYS_RW = r"\textsc{CortenMM}$_\mathrm{rw}$"
SYS_ADV = r"\textsc{CortenMM}$_\mathrm{adv}$"

SYS_BASE = r"adv$_\mathrm{base}$"
SYS_DVA = r"adv$_{+\mathrm{vpa}}$"

SYS_RW_TC = r"\textsc{CortenMM}$_\mathrm{rw}$-\texttt{tc}"
SYS_ADV_TC = r"\textsc{CortenMM}$_\mathrm{adv}$-\texttt{tc}"
SYS_RW_PT = r"\textsc{CortenMM}$_\mathrm{rw}$-\texttt{pt}"
SYS_ADV_PT = r"\textsc{CortenMM}$_\mathrm{adv}$-\texttt{pt}"

LINUX = "Linux"
LINUX_TC = r"Linux-\texttt{tc}"
LINUX_PT = r"Linux-\texttt{pt}"

def common_plt_setting():
    import matplotlib.pyplot as plt
    
    plt.rcParams.update({
        "text.usetex": True,
        "text.latex.preamble": r"\usepackage{libertine}", # Use Libertine font
        "font.family": "serif",
        "mathtext.fontset": "stix",
        "axes.linewidth": 0.5,
        'legend.fontsize': 8,
        'legend.handlelength': 2,
        'legend.frameon': False,
        'lines.linewidth': 0.8,  # Line plot linewidth
        'patch.linewidth': 0.5,  # Bar plot edge linewidth
        'hatch.linewidth': 0.5,  # Match hatch linewidth to patch linewidth
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
    })

def common_ax_setting(ax):
    # Add grid
    ax.grid(which='major', linestyle='--', linewidth=0.5, alpha=0.5)

    # Remove the top and right frame
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

def get_presets():
    # Color palette based on the GNUPLOT script
    colors = {
        1: "#D55E00",  # vermilion
        2: "#009E73",  # green
        3: "#C0A432",  # yellow
        4: "#0072B2",  # blue
        5: "#56B4E9",  # skyblue
        6: "#D35FB7",  # purple
        7: "#CC79A7",  # pink
        8: "#4B0082",  # indigo
        9: "#E69F00",  # orange
    }
    
    # Line/marker styles mapping
    line_styles = {
        1: '-',        # solid
        2: '--',       # dashed
        3: ':',        # dotted
        4: '-.',       # dash-dot
        5: (0, (3, 1, 1, 1)),  # custom dash-dot-dot
        6: (0, (3, 1, 1, 1, 1, 1)),  # custom dash-dot-dot-dot
        7: (0, (5, 1)),  # custom long dash
        8: (0, (1, 1)),  # custom short dash
        9: (0, (1, 1, 1, 1))  # custom short dash-dot
    }
    
    # Marker styles
    markers = {
        1: '^',
        2: 'd',
        3: 'v',
        4: 'x',
        5: '+',
        6: '1',
        7: '*',
        8: ',',
        9: 'p',
    }
    
    # Hatch patterns for bar plots
    hatches = {
        1: '',
        2: '\\\\\\\\',
        3: '....',
        4: 'xxxx',
        5: '++++',
        6: 'oooo',
        7: '----',
        8: 'OOOO',
        9: '****',
    }
    
    # Return an array of preset maps
    presets = [
        {
            'color': colors[i],
            'linestyle': line_styles[i],
            'marker': markers[i],
            'hatch': hatches[i]
        }
        for i in range(1, 10)
    ]

    return presets

def styled_bar(bar_fn, x, y, color, hatch, color_hatch_only=True, **kwargs):
    """
    A wrapper function for bar plotting with consistent styling.
    
    Parameters:
    - bar_fn: The bar plotting function (e.g., plt.bar, plt.barh).
    - x: The x-coordinates of the bars.
    - y: The heights (or widths) of the bars.
    - color: The color of the bars.
    - hatch: The hatch pattern for the bars.
    - **kwargs: Additional keyword arguments for the bar function.
    
    Returns:
    - The bar container object.
    """
    if color_hatch_only:
        try:
            # Need nightly matplotlib (>=3.11.0)
            r'''# python -m pip install \                                                                                                                                                       (main) 
                    --upgrade \
                    --pre \
                    --index-url https://pypi.anaconda.org/scientific-python-nightly-wheels/simple \
                    --extra-index-url https://pypi.org/simple \
                    matplotlib
            '''
            bar_fn(x, y, facecolor='none', hatch=hatch, hatchcolor=color, edgecolor='black', **kwargs)
        except:
            # Fallback for older versions of matplotlib that don't support hatchcolor
            bar_fn(x, y, facecolor='none', hatch=hatch, edgecolor=color, **kwargs)
    else:
        bar_fn(x, y, facecolor=color, hatch=hatch, edgecolor='black', **kwargs)

    return 

def get_experiment_output_dir():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "../../experiment_outputs/")

def find_and_read_latest_experiment_output(bench_name, sys_name):
    import os
    import re

    output_dir = get_experiment_output_dir()
    pattern = re.compile(rf"{bench_name}_{sys_name}_(\d{{14}})\.log")
    latest_file = None
    latest_timestamp = None

    for filename in os.listdir(output_dir):
        match = pattern.match(filename)
        if match:
            timestamp = match.group(1)
            if latest_timestamp is None or timestamp > latest_timestamp:
                latest_timestamp = timestamp
                latest_file = filename
    if latest_file is None:
        print(f"ERROR: No log file found for {bench_name} and {sys_name}.")
        return None
    
    path = os.path.join(output_dir, latest_file)

    try:
        with open(path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"ERROR: File {path} not found.")
        return None

    return content
