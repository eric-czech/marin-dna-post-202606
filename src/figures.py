"""Render figures from the transfer-validation CSV.

Figure 1: eval/loss vs learning_rate (single panel).
Figure 2: eval/loss vs beta2 / epsilon (1x2 panels).

Both figures union v0.14 + v0.15 runs and color by parameter scale. Per-scale
lines connect (axis-value -> mean eval/loss) so duplicate axis values across
versions don't zig-zag the line; individual runs are still scattered.

Usage:
    uv run src/figures.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "transfer_validation_results.csv"
SCALING_RESULTS_PATH = ROOT / "data" / "parameter_scaling_results.csv"
SCALING_HISTORY_PATH = ROOT / "data" / "parameter_scaling_history.csv"
FIGURES_DIR = ROOT / "figures"

# Constant width across all figures so they line up in any side-by-side rendering.
FIGURE_WIDTH = 12.0
FIGURE_HEIGHT = 5.0

# Top of the legend boxes in figure coordinates. Tuned so the legends sit just
# below the x-axis tick labels, not at the bottom of the figure.
_LEGEND_Y = 0.10

# Padding between x tick labels and the x-axis label (matplotlib default is 4).
_X_LABEL_PAD = 0

CONTROL_ROLES = ("positive-control", "negative-control")


def _params_label(num_params: int | float) -> str:
    n = int(num_params)
    if n >= 1_000_000_000:
        return f"{round(n / 1e9)}B"
    return f"{round(n / 1e6)}M"


def _fmt_lr(lr: float) -> str:
    exp = int(np.floor(np.log10(lr)))
    mantissa = lr / (10**exp)
    return rf"${mantissa:.1f}\times 10^{{{exp}}}$"


def _fmt_beta2(b: float) -> str:
    return f"{b:.4f}"


def _fmt_epsilon(e: float) -> str:
    if e <= 0:
        return f"{e:g}"
    exp = int(np.floor(np.log10(e)))
    mantissa = e / (10**exp)
    return rf"${mantissa:.1f}\times 10^{{{exp}}}$"


def _interpolate_x(value: float, grid_values: list[float], grid_xs: list[int], log_scale: bool) -> float:
    """Map a hparam value to an evenly-spaced grid x (log/linear). Extrapolates."""
    if log_scale:
        t = math.log(value)
        gt = [math.log(g) for g in grid_values]
    else:
        t, gt = value, list(grid_values)
    if t <= gt[0]:
        slope = (grid_xs[1] - grid_xs[0]) / (gt[1] - gt[0])
        return grid_xs[0] + slope * (t - gt[0])
    if t >= gt[-1]:
        slope = (grid_xs[-1] - grid_xs[-2]) / (gt[-1] - gt[-2])
        return grid_xs[-1] + slope * (t - gt[-1])
    for i in range(len(gt) - 1):
        if gt[i] <= t <= gt[i + 1]:
            frac = (t - gt[i]) / (gt[i + 1] - gt[i])
            return grid_xs[i] + frac * (grid_xs[i + 1] - grid_xs[i])
    return grid_xs[-1]


def _palette(param_counts: list[int]) -> dict[int, tuple]:
    cmap = plt.get_cmap("viridis")
    if len(param_counts) == 1:
        return {param_counts[0]: cmap(0.5)}
    return {p: cmap(0.15 + 0.7 * i / (len(param_counts) - 1)) for i, p in enumerate(param_counts)}


def _plot_axis(
    ax,
    df: pd.DataFrame,
    *,
    axis_role: str,
    axis_field: str,
    axis_label: str,
    log_scale: bool,
    value_formatter,
    palette: dict,
) -> None:
    """Plot eval/loss vs `axis_field` for the relevant rows. One series per param scale.

    Includes:
      - sweep points for runs with role == axis_role  (circles)
      - per-scale positive-control                    (square, on grid center)
      - 1B-only negative-control                      (square, x-position interpolated)
    """
    sub = df[df["role"].isin([axis_role, *CONTROL_ROLES])].dropna(subset=[axis_field, "eval_loss"]).copy()

    # Union x grid: every unique axis value seen in sweep + positive-control. Negative
    # control's value is interpolated on top of this grid (it's untransferred).
    grid_mask = sub["role"].isin([axis_role, "positive-control"])
    grid_values = sorted(sub.loc[grid_mask, axis_field].unique().tolist())
    grid_xs = list(range(len(grid_values)))
    grid_lookup = {v: i for i, v in enumerate(grid_values)}

    for params in sorted(sub["params"].unique()):
        scale = sub[sub["params"] == params]
        color = palette[int(params)]

        # Per-scale line: connect mean eval/loss at each axis value, ascending.
        line_pts = (
            scale[scale["role"].isin([axis_role, "positive-control"])]
            .groupby(axis_field, as_index=False)["eval_loss"].mean()
            .sort_values(axis_field)
        )
        if not line_pts.empty:
            line_xs = [grid_lookup[v] for v in line_pts[axis_field]]
            ax.plot(line_xs, line_pts["eval_loss"].values, color=color, linewidth=1, alpha=0.6, zorder=2)

        # Sweep points: circles, raw individual runs.
        sweep = scale[scale["role"] == axis_role]
        if not sweep.empty:
            sweep_xs = [grid_lookup[v] for v in sweep[axis_field]]
            ax.scatter(
                sweep_xs, sweep["eval_loss"].values,
                s=42, color=color, marker="o", edgecolors="k", linewidths=0.4, zorder=3,
            )

        # Positive control: square, sits at the grid center value (same for every scale).
        pos = scale[scale["role"] == "positive-control"]
        if not pos.empty:
            pos_xs = [grid_lookup[v] for v in pos[axis_field]]
            ax.scatter(
                pos_xs, pos["eval_loss"].values,
                s=70, color=color, marker="s", edgecolors="k", linewidths=0.6, zorder=4,
            )

        # Negative control (1B only): diamond at the (interpolated) untransferred value.
        neg = scale[scale["role"] == "negative-control"]
        if not neg.empty:
            for _, row in neg.iterrows():
                x = _interpolate_x(float(row[axis_field]), grid_values, grid_xs, log_scale)
                ax.scatter(
                    [x], [row["eval_loss"]],
                    s=80, color=color, marker="D", edgecolors="k", linewidths=0.6, zorder=4,
                )

    ax.set_xticks(grid_xs)
    ax.set_xticklabels([value_formatter(v) for v in grid_values], rotation=30, ha="right", fontsize=8)
    ax.set_xlabel(axis_label, labelpad=_X_LABEL_PAD)
    ax.set_ylabel("loss")
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)


def _shape_legend_handles():
    """Proxy artists for the marker-shape legend (no axes side-effects)."""
    common = dict(color="w", markerfacecolor="lightgray", markeredgecolor="k", markeredgewidth=0.6, linestyle="")
    sweep = Line2D([0], [0], marker="o", markersize=7, **common)
    optimal = Line2D([0], [0], marker="s", markersize=8, **common)
    reference = Line2D([0], [0], marker="D", markersize=8, **common)
    return [sweep, optimal, reference], ["sweep", "optimal (predicted)", "control (reference)"]


def _params_legend_handles(palette: dict, params: list[int]):
    """Proxy artists for the per-scale params legend (square markers, scale color)."""
    sorted_params = sorted(params)
    handles = [
        Line2D(
            [0], [0], marker="s", color="w", markerfacecolor=palette[p],
            markeredgecolor="k", markeredgewidth=0.6, markersize=8, linestyle="",
        )
        for p in sorted_params
    ]
    labels = [_params_label(p) for p in sorted_params]
    return handles, labels


# Tight label↔marker spacing, generous between (marker, label) pairs.
_LEGEND_KW = dict(
    fontsize=9,
    title_fontsize=9,
    frameon=True,
    handletextpad=0.3,
    columnspacing=2.2,
    borderpad=0.4,
)


def _attach_params_legend_below(fig, palette: dict, params: list[int], *, width_scale: float = 1.0) -> None:
    """Single horizontal `model params` legend, centered just below the x-axis.

    `width_scale` shrinks/expands the inter-pair gap (columnspacing) — smaller
    values produce a more compact legend.
    """
    p_handles, p_labels = _params_legend_handles(palette, params)
    kw = {**_LEGEND_KW, "columnspacing": _LEGEND_KW["columnspacing"] * width_scale}
    fig.legend(
        p_handles, p_labels,
        ncol=len(p_handles), title="model params",
        loc="upper center", bbox_to_anchor=(0.5, _LEGEND_Y),
        **kw,
    )


def _attach_legends_below(fig, palette: dict, params: list[int]) -> None:
    """Two horizontal figure-level legends below the axes:
       1. left  — `model params` (one square per scale)
       2. right — marker shape (sweep / control)
    """
    p_handles, p_labels = _params_legend_handles(palette, params)
    s_handles, s_labels = _shape_legend_handles()

    leg_params = fig.legend(
        p_handles, p_labels,
        ncol=len(p_handles), title="model params",
        loc="upper right", bbox_to_anchor=(0.41, _LEGEND_Y),
        **_LEGEND_KW,
    )
    fig.add_artist(leg_params)
    fig.legend(
        s_handles, s_labels,
        ncol=len(s_handles), title="run type",
        loc="upper left", bbox_to_anchor=(0.43, _LEGEND_Y),
        **_LEGEND_KW,
    )


def _save(fig, name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png = FIGURES_DIR / f"{name}.png"
    pdf = FIGURES_DIR / f"{name}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    print(f"Wrote {png} and {pdf}")


def figure1_lr(df: pd.DataFrame, palette: dict, params: list[int]) -> None:
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    _plot_axis(
        ax, df,
        axis_role="learning_rate",
        axis_field="learning_rate",
        axis_label=r"learning rate ($\eta$)",
        log_scale=True,
        value_formatter=_fmt_lr,
        palette=palette,
    )
    ax.set_title("Transfer validation — loss vs learning rate")
    # Reserve room for the legends below.
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    _attach_legends_below(fig, palette, params)
    _save(fig, "figure1_lr_transfer")


def figure2_beta2_epsilon(df: pd.DataFrame, palette: dict, params: list[int]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    _plot_axis(
        axes[0], df,
        axis_role="beta2",
        axis_field="beta2",
        axis_label=r"$\beta_2$",
        log_scale=False,
        value_formatter=_fmt_beta2,
        palette=palette,
    )
    # Push the β₂ label down slightly relative to the global label pad.
    axes[0].xaxis.labelpad = 4
    _plot_axis(
        axes[1], df,
        axis_role="epsilon",
        axis_field="epsilon",
        axis_label=r"$\epsilon$",
        log_scale=True,
        value_formatter=_fmt_epsilon,
        palette=palette,
    )
    # Pull the ε label up closer to the tick labels.
    axes[1].xaxis.labelpad = -4
    fig.suptitle(r"Transfer validation — loss vs $\beta_2$ and $\epsilon$", fontsize=11, y=0.95)
    fig.tight_layout(rect=(0, 0.08, 1, 0.99))
    _attach_legends_below(fig, palette, params)
    _save(fig, "figure2_beta2_epsilon_transfer")


# Eval VEP sample sizes per variant type (from docs/outline.md). Embedded in
# Figure 5's panel titles. Figure 4 reuses the same ordering for consistency.
VEP_PANELS: tuple[tuple[str, str, int], ...] = (
    ("missense_variant", "missense", 14800),
    ("tss_proximal", "promoter", 1800),
    ("5_prime_UTR_variant", "5' UTR", 2100),
    ("3_prime_UTR_variant", "3' UTR", 770),
    ("splicing", "splicing", 2670),
    ("synonymous_variant", "synonymous", 460),
)
_MARKER_AREA = 110.0


def figure4_params_vs_auprc(results: pd.DataFrame) -> None:
    """Single panel, line+scatter: model params (log-x) vs AUPRC, one series per variant type."""
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    cmap = plt.get_cmap("tab10")
    handles: list = []
    labels: list[str] = []
    for i, (subset, label, _n) in enumerate(VEP_PANELS):
        col = f"lm_eval/traitgym_mendelian_v2_255/{subset}/auprc"
        valid = results.dropna(subset=["params", col]).sort_values("params")
        line, = ax.plot(
            valid["params"], valid[col],
            marker="o", linestyle="-", color=cmap(i),
            linewidth=1.3, markersize=6, markeredgecolor="k", markeredgewidth=0.4,
            zorder=3,
        )
        handles.append(line)
        labels.append(label)
    ax.set_xscale("log")
    ax.set_xlabel("model params", labelpad=_X_LABEL_PAD)
    ax.set_ylabel("AUPRC")
    ax.grid(True, which="both", alpha=0.25, linewidth=0.5)
    ax.set_title("Parameter scaling — params vs VEP AUPRC by variant type")
    fig.tight_layout(rect=(0, 0.08, 1, 1))

    fig.legend(
        handles, labels,
        ncol=len(handles), title="variant type",
        loc="upper center", bbox_to_anchor=(0.5, _LEGEND_Y),
        **_LEGEND_KW,
    )
    _save(fig, "figure4_params_vs_vep_auprc")


def figure5_loss_vs_auprc(results: pd.DataFrame, palette: dict) -> None:
    """2x3 scatter: final eval/loss (x) vs lm_eval AUPRC (y) for six VEP subsets.

    Marker color encodes params; size is uniform.
    """
    fig, axes = plt.subplots(2, 3, figsize=(FIGURE_WIDTH, 6.5))
    for ax, (subset, title, n) in zip(axes.flat, VEP_PANELS, strict=True):
        col = f"lm_eval/traitgym_mendelian_v2_255/{subset}/auprc"
        valid = results.dropna(subset=["eval_loss", col]).sort_values("params")
        for _, row in valid.iterrows():
            p = int(row["params"])
            ax.scatter(
                row["eval_loss"], row[col],
                s=_MARKER_AREA, color=palette[p], edgecolors="k", linewidths=0.5, zorder=3,
            )
        # Dotted linear best-fit + subtle Pearson ρ annotation.
        if len(valid) >= 2:
            xs = valid["eval_loss"].to_numpy(dtype=float)
            ys = valid[col].to_numpy(dtype=float)
            slope, intercept = np.polyfit(xs, ys, 1)
            x_line = np.array([xs.min(), xs.max()])
            ax.plot(x_line, slope * x_line + intercept, linestyle=":", color="0.35", linewidth=1.2, zorder=2)
            rho = float(np.corrcoef(xs, ys)[0, 1])
            ax.text(
                0.97, 0.95, rf"$\rho={rho:.2f}$",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=8, color="0.35",
            )
        ax.set_title(f"{title} (n={n:,})", fontsize=10)
        ax.grid(True, alpha=0.25, linewidth=0.5)

    # Shared axis labels: "loss" on the bottom row only, "AUPRC" on the leftmost column only.
    for ax in axes[-1, :]:
        ax.set_xlabel("loss", labelpad=_X_LABEL_PAD)
    for ax in axes[:, 0]:
        ax.set_ylabel("AUPRC")

    fig.suptitle("Parameter scaling — loss vs VEP AUPRC by variant type", fontsize=11, y=0.96)
    fig.tight_layout(rect=(0, 0.08, 1, 0.98))

    params_present = sorted({int(p) for p in results["params"].dropna().unique()})
    _attach_params_legend_below(fig, palette, params_present, width_scale=0.55)
    _save(fig, "figure5_loss_vs_vep_auprc")


def figure3_loss_curves(history: pd.DataFrame, results: pd.DataFrame, palette: dict) -> None:
    """1x2: train loss / eval loss curves vs step (log-log), one line per param scale."""
    name_to_params = dict(zip(results["run_name"], results["params"], strict=True))
    history = history.assign(params=history["run_name"].map(name_to_params))
    # Log-x cannot show step=0; the step-0 eval is pre-training and not informative anyway.
    history = history[history["step"] > 0]

    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    panels = [
        (axes[0], "train/loss", "train loss"),
        (axes[1], "eval/loss", "eval loss"),
    ]
    for ax, metric, ylabel in panels:
        sub = history[history["metric"] == metric]
        for params in sorted(sub["params"].unique()):
            line = sub[sub["params"] == params].sort_values("step")
            ax.plot(line["step"], line["value"], color=palette[int(params)], linewidth=1.3)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("step", labelpad=_X_LABEL_PAD)
        ax.set_ylabel(ylabel)
        ax.grid(True, which="both", alpha=0.25, linewidth=0.5)

    fig.suptitle("Parameter scaling — loss vs step", fontsize=11, y=0.95)
    fig.tight_layout(rect=(0, 0.08, 1, 0.99))

    params_present = sorted({int(p) for p in history["params"].dropna().unique()})
    _attach_params_legend_below(fig, palette, params_present, width_scale=0.55)
    _save(fig, "figure3_scaling_loss_curves")


def main() -> None:
    transfer_df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(transfer_df)} rows from {DATA_PATH}")
    scaling_results = pd.read_csv(SCALING_RESULTS_PATH)
    print(f"Loaded {len(scaling_results)} rows from {SCALING_RESULTS_PATH}")
    scaling_history = pd.read_csv(SCALING_HISTORY_PATH)
    print(f"Loaded {len(scaling_history)} rows from {SCALING_HISTORY_PATH}")

    # Per-sweep palettes so each figure's colors span the full viridis range.
    # Sharing a single palette across both compresses the transfer scales (only 3
    # of 8 positions) into a narrow color band that's hard to distinguish.
    transfer_params = sorted({int(p) for p in transfer_df["params"].dropna().unique()})
    transfer_palette = _palette(transfer_params)
    scaling_params = sorted({int(p) for p in scaling_results["params"].dropna().unique()})
    scaling_palette = _palette(scaling_params)

    figure1_lr(transfer_df, transfer_palette, transfer_params)
    figure2_beta2_epsilon(transfer_df, transfer_palette, transfer_params)
    figure3_loss_curves(scaling_history, scaling_results, scaling_palette)
    figure4_params_vs_auprc(scaling_results)
    figure5_loss_vs_auprc(scaling_results, scaling_palette)


if __name__ == "__main__":
    main()
