"""Figure 3: per-region transfer loss vs each tuned hyper (3x3 panels)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from figures.data import save
from utils.figure_style import (
    FIGURE_WIDTH,
    attach_legends_below,
    figsize,
    fmt_beta2,
    fmt_epsilon,
    fmt_lr,
)
from utils.sweep_panel import plot_axis

# Rows of figure 3: (region key, label used in axis text / row title).
_REGION_ROWS: tuple[tuple[str, str], ...] = (
    ("cds", "CDS"),
    ("upstream", "upstream"),
    ("downstream", "downstream"),
)
# Cols of figure 3: (axis role, axis field, axis label, log scale, formatter).
_HYPER_COLS: tuple[tuple[str, str, str, bool, "callable"], ...] = (
    ("learning_rate", "learning_rate", r"learning rate ($\eta$)", True, fmt_lr),
    ("beta2", "beta2", r"$\beta_2$", False, fmt_beta2),
    ("epsilon", "epsilon", r"$\epsilon$", True, fmt_epsilon),
)


def build(df: pd.DataFrame, palette: dict, params: list[int]) -> None:
    """3x3 grid: per-region transfer loss vs each tuned hyper.

    Rows are genomic regions (CDS / upstream / downstream); columns are the
    swept hypers (learning rate / β₂ / ε). y is `eval/val_<region>/loss` from
    the corresponding region column in the transfer CSV. Free y-axis per cell.
    Negative controls are omitted (this figure focuses on transfer-vs-direct
    sweep shapes per region).
    """
    fig, axes = plt.subplots(3, 3, figsize=figsize(FIGURE_WIDTH, 8.0))
    for r, (region_key, region_label) in enumerate(_REGION_ROWS):
        y_field = f"eval_loss_{region_key}"
        for c, (axis_role, axis_field, axis_label, log_scale, fmt) in enumerate(_HYPER_COLS):
            ax = axes[r, c]
            plot_axis(
                ax, df,
                axis_role=axis_role,
                axis_field=axis_field,
                axis_label=axis_label if r == 2 else "",
                log_scale=log_scale,
                value_formatter=fmt,
                palette=palette,
                include_negative_control=False,
                y_field=y_field,
                y_label="loss" if c == 0 else "",
            )
            if r != 2:
                ax.set_xticklabels([])
                ax.set_xlabel("")
            if c == 0:
                # Row label on the left, outside the axes.
                ax.annotate(
                    region_label,
                    xy=(-0.22, 0.5), xycoords="axes fraction",
                    rotation=90, ha="center", va="center",
                    fontsize=11, fontweight="bold",
                )
    fig.suptitle(
        "Transfer validation — per-region loss vs learning rate, $\\beta_2$, and $\\epsilon$",
        fontsize=11, y=0.985,
    )
    # Explicit margins (no tight_layout) so the title and legend hug the plot grid tightly.
    fig.subplots_adjust(top=0.9525, bottom=0.1225, left=0.055, right=0.99, hspace=0.12, wspace=0.18)
    # Centered, tightly-spaced two-legend strip at the bottom (shared helper).
    attach_legends_below(fig, palette, params, include_reference=False, legend_y=0.03)
    save(fig, "figure3_region_hyper_transfer")
