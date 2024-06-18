from pathlib import Path
from itertools import cycle

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_recovery(recovery: pd.DataFrame, savedir: Path) -> None:

    colors = cycle(["magenta", "blue", "darkorange", "limegreen", "black"])
    fig, axs = plt.subplots(5, 1, sharex=True, figsize=(10, 10))
    for ax, metric in zip(axs.flatten(), recovery.columns):
        ax.plot(recovery.index, recovery.loc[:, metric], color=next(colors))
        ax.set_title(metric)

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H"))
        ax.xaxis.set_major_locator(plt.MaxNLocator(12))

        for tick in ax.get_xticklabels():
            tick.set_rotation(45)

    fig.tight_layout()
    fig.savefig(savedir / "recovery", dpi=300, bbox_inches="tight")
