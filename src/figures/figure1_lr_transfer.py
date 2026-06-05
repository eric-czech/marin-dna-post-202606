"""Figure 1: transfer-validation loss vs learning rate (single panel)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from figures.data import save
from utils.figure_style import FIGURE_HEIGHT, FIGURE_WIDTH, attach_legends_below, figsize, fmt_lr
from utils.sweep_panel import plot_axis

# Compact (N, D, C) summary contrasting the small-scale reference Vizier sweep
# with the larger transfer-validation sweep depicted in Figures 1 & 2.
# Numbers come from docs/outline.md (`### Sweeps` + `#### Transfer validation
# sweep`); validation N and C are shown as ranges across the three scales.
_TRANSFER_SUBTITLE = (
    r"$N{=}25\mathrm{M},\,D{=}2.5\mathrm{B},\,C{=}4{\times}10^{17}$"
    r"$\,\rightarrow\,$"
    r"$N{=}255\mathrm{M}{-}1\mathrm{B},\,D{=}10\mathrm{B},\,C{=}1.6{-}6.8{\times}10^{19}$"
)


def build(df: pd.DataFrame, palette: dict, params: list[int]) -> None:
    # Single-panel figure narrower than the multi-panel default to avoid stretching.
    fig, ax = plt.subplots(figsize=figsize(FIGURE_WIDTH * 0.8, FIGURE_HEIGHT))
    plot_axis(
        ax, df,
        axis_role="learning_rate",
        axis_field="learning_rate",
        axis_label=r"learning rate ($\eta$)",
        log_scale=True,
        value_formatter=fmt_lr,
        palette=palette,
    )
    ax.set_title("Transfer validation — loss vs learning rate\n" + _TRANSFER_SUBTITLE, fontsize=11)
    # Reserve room for the legends below.
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    attach_legends_below(fig, palette, params)
    save(fig, "figure1_lr_transfer")
