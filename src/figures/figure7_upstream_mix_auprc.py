"""Figure 7: continued-pretraining mixture shift — VEP AUPRC vs upstream proportion.

Eight `uniform_to_upstream_*` continuations all warm-start from the 1·L uniform
run, then train mixes ranging from upstream-heavy (U90) down to no-upstream
(C50/D50). We plot the change in composite 6-task VEP AUPRC relative to the 1·L
uniform run against the upstream proportion of the continuation mix — i.e. how
far shifting the mixture off uniform moves VEP performance. `uniform_to_uniform_1`
(1.7·L) is omitted: it repeats the ⅓ mix at a larger token budget.
"""

from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt

from figures import mixture_lineage as ml
from figures.data import save
from utils.figure_style import X_LABEL_PAD

# The uniform→upstream sweep (1.7·L uniform_to_uniform_1 omitted), and the
# uniform run all of them continue from.
UPSTREAM_SWEEP = (
    "uniform_to_upstream_1",    # 1.1  U90
    "uniform_to_upstream_2",    # 1.2  U80
    "uniform_to_upstream_3",    # 1.3  U60
    "uniform_to_upstream_3.5",  # 1.4  U50
    "uniform_to_upstream_3.6",  # 1.5  U40
    "uniform_to_upstream_3.7",  # 1.6  U33
    "uniform_to_upstream_4",    # 1.8  U30
    "uniform_to_upstream_5",    # 1.9  U0
)
BASELINE = "uniform"


def build(df: pd.DataFrame) -> None:
    score = {row["mix"]: ml.composite_score(row) for _, row in df.iterrows()}
    base = score[BASELINE]

    pts = sorted(
        (ml.BY_MIX[mix].weights.get("upstream", 0.0), score[mix] - base)
        for mix in UPSTREAM_SWEEP
    )
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.axhline(0, color="0.4", lw=0.8, ls="--", zorder=1)
    ax.plot(
        xs, ys,
        color="#3B6FB6", lw=1.8, marker="o", markersize=8,
        markerfacecolor="#3B6FB6", markeredgecolor="k", markeredgewidth=0.5, zorder=3,
    )
    ax.text(
        max(xs), 0.0, "uniform (1·L)  ", ha="right", va="bottom",
        fontsize=8, color="0.4",
    )
    ax.set_xlabel("upstream proportion in continuation mix", labelpad=X_LABEL_PAD)
    ax.set_ylabel(r"$\Delta$ composite VEP AUPRC vs uniform")
    ax.set_title("Continued pretraining from uniform — VEP AUPRC vs upstream proportion", fontsize=11)
    ax.grid(True, alpha=0.25, linewidth=0.5)

    fig.tight_layout()
    save(fig, "figure7_upstream_mix_auprc")
