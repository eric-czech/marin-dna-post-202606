"""Shared presentation helpers for the figure set.

Figure dimensions, the viridis param palette, value formatters, the
below-axes legend strips, and tick formatting — everything that controls how
the figures *look* but not what data they show.
"""

from __future__ import annotations

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter
import matplotlib.pyplot as plt

# Constant width across all figures so they line up in any side-by-side rendering.
FIGURE_WIDTH = 12.0
FIGURE_HEIGHT = 5.0

# Top of the legend boxes in figure coordinates. Tuned so the legends sit just
# below the x-axis tick labels, not at the bottom of the figure.
LEGEND_Y = 0.10

# Padding between x tick labels and the x-axis label (matplotlib default is 4).
X_LABEL_PAD = 0

# Tight label↔marker spacing, generous between (marker, label) pairs.
LEGEND_KW = dict(
    fontsize=9,
    title_fontsize=9,
    frameon=False,
    handletextpad=0.3,
    columnspacing=2.2,
    borderpad=0.4,
)


def palette(param_counts: list[int]) -> dict[int, tuple]:
    cmap = plt.get_cmap("viridis")
    if len(param_counts) == 1:
        return {param_counts[0]: cmap(0.5)}
    return {p: cmap(0.15 + 0.7 * i / (len(param_counts) - 1)) for i, p in enumerate(param_counts)}


def params_label(num_params: int | float) -> str:
    n = int(num_params)
    if n >= 1_000_000_000:
        return f"{round(n / 1e9)}B"
    return f"{round(n / 1e6)}M"


def fmt_lr(lr: float) -> str:
    exp = int(np.floor(np.log10(lr)))
    mantissa = lr / (10**exp)
    return rf"${mantissa:.1f}\times 10^{{{exp}}}$"


def fmt_beta2(b: float) -> str:
    return f"{b:.4f}"


def fmt_epsilon(e: float) -> str:
    if e <= 0:
        return f"{e:g}"
    exp = int(np.floor(np.log10(e)))
    mantissa = e / (10**exp)
    return rf"${mantissa:.1f}\times 10^{{{exp}}}$"


def shape_legend_handles(include_reference: bool = True):
    """Proxy artists for the marker-shape legend (no axes side-effects)."""
    common = dict(color="w", markerfacecolor="lightgray", markeredgecolor="k", markeredgewidth=0.6, linestyle="")
    sweep = Line2D([0], [0], marker="o", markersize=8, **common)
    optimal = Line2D([0], [0], marker="s", markersize=8, **common)
    handles = [sweep, optimal]
    labels = ["sweep", "optimal (predicted)"]
    if include_reference:
        handles.append(Line2D([0], [0], marker="D", markersize=8, **common))
        labels.append("control (reference)")
    return handles, labels


def params_legend_handles(palette: dict, params: list[int]):
    """Proxy artists for the per-scale params legend (square markers, scale color)."""
    sorted_params = sorted(params)
    handles = [
        Line2D(
            [0], [0], marker="s", color="w", markerfacecolor=palette[p],
            markeredgecolor="k", markeredgewidth=0.6, markersize=8, linestyle="",
        )
        for p in sorted_params
    ]
    labels = [params_label(p) for p in sorted_params]
    return handles, labels


def attach_params_legend_below(fig, palette: dict, params: list[int], *, width_scale: float = 1.0) -> None:
    """Single horizontal `model params` legend, centered just below the x-axis.

    `width_scale` shrinks/expands the inter-pair gap (columnspacing) — smaller
    values produce a more compact legend.
    """
    p_handles, p_labels = params_legend_handles(palette, params)
    kw = {**LEGEND_KW, "columnspacing": LEGEND_KW["columnspacing"] * width_scale}
    fig.legend(
        p_handles, p_labels,
        ncol=len(p_handles), title="model params",
        loc="upper center", bbox_to_anchor=(0.5, LEGEND_Y),
        **kw,
    )


def attach_legends_below(
    fig, palette: dict, params: list[int],
    include_reference: bool = True,
    legend_y: float = LEGEND_Y,
) -> None:
    """Two horizontal figure-level legends below the axes:
       1. left  — `model params` (one square per scale)
       2. right — marker shape (sweep / control)
    """
    p_handles, p_labels = params_legend_handles(palette, params)
    s_handles, s_labels = shape_legend_handles(include_reference=include_reference)

    leg_params = fig.legend(
        p_handles, p_labels,
        ncol=len(p_handles), title="model params",
        loc="upper right", bbox_to_anchor=(0.41, legend_y),
        **LEGEND_KW,
    )
    fig.add_artist(leg_params)
    fig.legend(
        s_handles, s_labels,
        ncol=len(s_handles), title="run type",
        loc="upper left", bbox_to_anchor=(0.43, legend_y),
        **LEGEND_KW,
    )


def set_plain_decimal_yticks(ax) -> None:
    """Force y-axis tick labels to plain decimals (no scientific notation).

    Works for both linear and log y-scales. On log scales matplotlib's default
    LogFormatter renders values like ``6×10⁻¹``; in this figure's loss range
    (~0.5–1.5) plain decimals are more readable.
    """
    fmt = ScalarFormatter()
    fmt.set_scientific(False)
    fmt.set_useOffset(False)
    ax.yaxis.set_major_formatter(fmt)
    ax.yaxis.set_minor_formatter(fmt)
