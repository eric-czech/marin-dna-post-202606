"""Continued pretraining: how does the training mix shift downstream auprc?

Five `dna-bolinas-mix-v0.9-p1B-i{10..14}-uniform_to_upstream_{1..5}` runs all
warm-start from the same uniform-mix (1/3 cds, 1/3 upstream, 1/3 downstream)
checkpoint, then continue training with these new mixes:

  variant   upstream  cds   downstream
  _1          0.90    0.05    0.05
  _2          0.80    0.10    0.10
  _3          0.60    0.20    0.20
  _4          0.30    0.35    0.35
  _5          0.00    0.50    0.50

For each run we read the first and last logged lm_eval/auprc values across six
TraitGym Mendelian variant tasks, plus a composite = average of the six.
Output is a 1x2 figure: composite begin->end (left) and per-constituent
begin->end (right), with one color per continuation mix.

Output:
  figures/appendix/continuation_mix_shift.{png,pdf}

Usage:
  uv run src/appendix/continuation_mix_shift.py
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import wandb

ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_DIR = ROOT / "figures" / "appendix"

WANDB_PROJECT = "eric-czech/marin"
TRAITGYM_PREFIX = "lm_eval/traitgym_mendelian_v2_255"

VARIANTS = (1, 2, 3, 4, 5)
RUN_NAMES = {
    i: f"dna-bolinas-mix-v0.9-p1B-i{9 + i}-uniform_to_upstream_{i}" for i in VARIANTS
}

# (upstream, cds, downstream) weights for the continuation mix.
MIXES: dict[int, tuple[float, float, float]] = {
    1: (0.90, 0.05, 0.05),
    2: (0.80, 0.10, 0.10),
    3: (0.60, 0.20, 0.20),
    4: (0.30, 0.35, 0.35),
    5: (0.00, 0.50, 0.50),
}

CONSTITUENTS: tuple[tuple[str, str], ...] = (
    ("tss_proximal", "TSS-proximal"),
    ("5_prime_UTR_variant", "5' UTR"),
    ("missense_variant", "missense"),
    ("splicing", "splicing"),
    ("synonymous_variant", "synonymous"),
    ("3_prime_UTR_variant", "3' UTR"),
)

FIGURE_WIDTH = 12.0
FIGURE_HEIGHT = 4.5


def _resolve(api: wandb.Api, name: str):
    runs = list(api.runs(WANDB_PROJECT, filters={"display_name": {"$regex": f"^{re.escape(name)}$"}}))
    if len(runs) == 0:
        raise RuntimeError(f"no run matching display_name {name!r}")
    if len(runs) > 1:
        runs.sort(key=lambda r: r.created_at, reverse=True)
        print(f"  WARN: {len(runs)} runs match {name!r}; taking newest = {runs[0].id}")
    return runs[0]


def fetch_data() -> dict:
    api = wandb.Api(timeout=300)
    auprc_keys = [f"{TRAITGYM_PREFIX}/{m}/auprc" for m, _ in CONSTITUENTS]
    out: dict[int, dict] = {}
    for variant in VARIANTS:
        name = RUN_NAMES[variant]
        print(f"fetching variant {variant}: {name}")
        run = _resolve(api, name)
        df = run.history(keys=auprc_keys, samples=10000)
        present = [k for k in auprc_keys if k in df.columns]
        df = df.dropna(how="all", subset=present).sort_values("_step").reset_index(drop=True)
        if df.empty:
            raise RuntimeError(f"variant {variant}: no lm_eval rows yet")
        first_row = df.iloc[0]
        last_row = df.iloc[-1]
        out[variant] = {
            "first_step": int(first_row["_step"]),
            "last_step": int(last_row["_step"]),
            "n_evals": len(df),
            "first": {k: float(first_row[k]) for k in auprc_keys},
            "last": {k: float(last_row[k]) for k in auprc_keys},
            "state": run.state,
        }
        print(
            f"  first_step={out[variant]['first_step']}, "
            f"last_step={out[variant]['last_step']}, "
            f"n_evals={out[variant]['n_evals']}, state={out[variant]['state']}"
        )
    return out


def _save(fig, name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    png = FIGURES_DIR / f"{name}.png"
    pdf = FIGURES_DIR / f"{name}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    print(f"saved {png}")
    print(f"saved {pdf}")


def plot(data: dict) -> None:
    xs = np.array([MIXES[v][0] for v in VARIANTS])  # upstream fraction
    order = np.argsort(xs)
    xs_sorted = xs[order]
    variants_sorted = [VARIANTS[i] for i in order]

    fig, (ax_comp, ax_cons) = plt.subplots(1, 2, figsize=(FIGURE_WIDTH, FIGURE_HEIGHT), sharex=True)

    deltas = []
    for v in variants_sorted:
        d = data[v]
        firsts = np.array([d["first"][f"{TRAITGYM_PREFIX}/{m}/auprc"] for m, _ in CONSTITUENTS])
        lasts = np.array([d["last"][f"{TRAITGYM_PREFIX}/{m}/auprc"] for m, _ in CONSTITUENTS])
        deltas.append(float(np.mean(lasts) - np.mean(firsts)))
    ax_comp.axhline(0, color="0.4", lw=0.8, ls="--", zorder=1)
    ax_comp.plot(
        xs_sorted, deltas,
        color="#3B6FB6", lw=1.8, marker="o", markersize=8,
        markerfacecolor="#3B6FB6", markeredgecolor="k", markeredgewidth=0.5, zorder=3,
    )
    ax_comp.set_xlabel("upstream proportion in continuation mix")
    ax_comp.set_ylabel(r"$\Delta$ composite auprc (end − begin)")
    ax_comp.set_title("Composite (mean of 6 metrics)", fontsize=11)
    ax_comp.grid(True, alpha=0.25, linewidth=0.5)

    cmap = plt.get_cmap("tab10")
    ax_cons.axhline(0, color="0.4", lw=0.8, ls="--", zorder=1)
    for i, (metric_key, label) in enumerate(CONSTITUENTS):
        full_key = f"{TRAITGYM_PREFIX}/{metric_key}/auprc"
        ys = [data[v]["last"][full_key] - data[v]["first"][full_key] for v in variants_sorted]
        ax_cons.plot(
            xs_sorted, ys,
            color=cmap(i), lw=1.5, marker="o", markersize=6,
            markerfacecolor=cmap(i), markeredgecolor="k", markeredgewidth=0.4,
            zorder=3, label=label,
        )
    ax_cons.set_xlabel("upstream proportion in continuation mix")
    ax_cons.set_ylabel(r"$\Delta$ auprc (end − begin)")
    ax_cons.set_title("Per-metric", fontsize=11)
    ax_cons.grid(True, alpha=0.25, linewidth=0.5)
    ax_cons.legend(loc="best", fontsize=8, frameon=True, ncol=2, title="metric", title_fontsize=8)

    for ax in (ax_comp, ax_cons):
        ax.set_xticks(xs_sorted)
        ax.set_xticklabels([f"{x:.2f}" for x in xs_sorted])

    fig.suptitle(
        "Continued pretraining from uniform-mix checkpoint — auprc shift vs upstream proportion",
        fontsize=12, y=0.985,
    )
    fig.tight_layout(rect=(0, 0.02, 1, 0.965))
    _save(fig, "continuation_mix_shift")


def main() -> None:
    data = fetch_data()
    plot(data)


if __name__ == "__main__":
    main()
