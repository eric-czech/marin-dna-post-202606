"""Lineage, mixture weights, and token accounting for the v0.9 mixture sweep.

This information is not recoverable from W&B alone — it's transcribed from the
marin experiment (`experiments/dna/exp135_bolinas_mix_sweep.py`). Each run is one
training stage; continuations warm-start from a parent checkpoint.

Naming (the `name` field, used as the figure label and a stable handle):
  - Tree-path id: root number + sibling indices (`1`, `1.7`, `1.7.1`). Dot count
    = depth; the path = the branch. Roots are separate trees (1=unif, 2=upstream
    -only, 3=cds-only, 4=downstream-only, 5=zoo, 6=zoo upstream-tilted).
  - Trailing `·S/M/L` = the run's OWN new-portion token budget (from the W&B
    `tokens` tag), set by `max_train_examples` to a per-region dataset size:
        S ≈ 5.2B  (downstream-dataset-sized)
        M ≈ 17.5B (upstream-dataset-sized)
        L ≈ 62B   (cds-dataset-sized)
    The base `unif` root (`1·L`) is ~52B (3×upstream caps, not via
    max_train_examples) and is grouped with L.

Branch types and token accounting:
  - "root"         — trained from scratch; no inherited tokens.
  - "pre_cooldown" — warm-started from a parent checkpoint taken before the
                     parent's cooldown (~80% of the parent's run).
  - "final"        — warm-started from a parent's final (fully-cooled) checkpoint.
  Inherited tokens scale the PARENT's own tokens by COOLDOWN_KEEP_FRACTION for a
  pre_cooldown branch (and by 1.0 for final); grandparent-and-earlier
  contributions always pass through at 100% (they precede every branch point).
  Note: one pre_cooldown branch (1.7.1) actually sits at ~68% of its parent, but
  per spec we use the flat 0.8 for all pre_cooldown branches.
"""

from __future__ import annotations

from dataclasses import dataclass

# Fraction of a parent's own tokens inherited when branching before its cooldown.
COOLDOWN_KEEP_FRACTION = 0.8

# Display order + single-letter codes for the five mixture components.
REGION_ORDER = ("cds", "upstream", "downstream", "ncrna_exon", "ccre_non_promoter")
REGION_LETTER = {
    "cds": "C", "upstream": "U", "downstream": "D",
    "ncrna_exon": "N", "ccre_non_promoter": "E",
}

# The 6 VEP subsets averaged into the composite score (matches Figs 5/6).
COMPOSITE_SUBSETS = (
    "missense_variant", "tss_proximal", "5_prime_UTR_variant",
    "3_prime_UTR_variant", "splicing", "synonymous_variant",
)

_THIRD = 1 / 3
_FIFTH = 1 / 5


@dataclass(frozen=True)
class Run:
    name: str                    # tree-path id + size tier (display label)
    mix: str                     # W&B `mix=` tag (join key to the CSV)
    weights: dict[str, float]    # training mixture weights over REGION_ORDER
    parent: str | None           # parent's `mix`, or None for roots
    branch: str                  # "root" | "pre_cooldown" | "final"


# Ordered so siblings appear left→right as a sweep (e.g. under `unif`, by upstream
# weight descending). Mirrors MIX_CONFIGS minus the dropped external-parent run.
LINEAGE: tuple[Run, ...] = (
    # Tree 1 — uniform (CUD ⅓) base, ~52B own.
    Run("1·L", "uniform", {"cds": _THIRD, "upstream": _THIRD, "downstream": _THIRD}, None, "root"),
    Run("1.1·S", "uniform_to_upstream_1", {"upstream": 0.9, "cds": 0.05, "downstream": 0.05}, "uniform", "pre_cooldown"),
    Run("1.2·S", "uniform_to_upstream_2", {"upstream": 0.8, "cds": 0.1, "downstream": 0.1}, "uniform", "pre_cooldown"),
    Run("1.3·S", "uniform_to_upstream_3", {"upstream": 0.6, "cds": 0.2, "downstream": 0.2}, "uniform", "pre_cooldown"),
    Run("1.4·M", "uniform_to_upstream_3.5", {"upstream": 0.5, "cds": 0.25, "downstream": 0.25}, "uniform", "final"),
    Run("1.5·M", "uniform_to_upstream_3.6", {"upstream": 0.4, "cds": 0.3, "downstream": 0.3}, "uniform", "final"),
    Run("1.6·M", "uniform_to_upstream_3.7", {"upstream": _THIRD, "cds": _THIRD, "downstream": _THIRD}, "uniform", "final"),
    Run("1.7·L", "uniform_to_uniform_1", {"upstream": _THIRD, "cds": _THIRD, "downstream": _THIRD}, "uniform", "pre_cooldown"),
    Run("1.8·S", "uniform_to_upstream_4", {"upstream": 0.3, "cds": 0.35, "downstream": 0.35}, "uniform", "pre_cooldown"),
    Run("1.9·S", "uniform_to_upstream_5", {"cds": 0.5, "downstream": 0.5}, "uniform", "pre_cooldown"),
    Run("1.5.1·M", "uniform_to_upstream_3.6.2", {"upstream": 0.4, "cds": 0.3, "downstream": 0.3}, "uniform_to_upstream_3.6", "final"),
    Run("1.7.1·M", "exp135-zoonomia-m2",
        {"cds": _FIFTH, "upstream": _FIFTH, "downstream": _FIFTH, "ncrna_exon": _FIFTH, "ccre_non_promoter": _FIFTH},
        "uniform_to_uniform_1", "pre_cooldown"),
    Run("1.7.2·L", "exp135-zoonomia-m5.1",
        {"cds": _FIFTH, "upstream": _FIFTH, "downstream": _FIFTH, "ncrna_exon": _FIFTH, "ccre_non_promoter": _FIFTH},
        "uniform_to_uniform_1", "final"),
    Run("1.7.1.1·M", "exp135-zoonomia-m4.1",
        {"cds": _FIFTH, "upstream": _FIFTH, "downstream": _FIFTH, "ncrna_exon": _FIFTH, "ccre_non_promoter": _FIFTH},
        "exp135-zoonomia-m2", "pre_cooldown"),
    # Tree 2 — upstream-only base, ~17.5B own.
    Run("2·M", "upstream_only", {"upstream": 1.0}, None, "root"),
    Run("2.1·S", "cont_upstream_to_cds_2", {"cds": 0.5, "upstream": 0.5}, "upstream_only", "final"),
    Run("2.2·S", "cont_upstream_to_cds_2.1", {"cds": 0.5, "upstream": 0.5}, "upstream_only", "final"),
    Run("2.3·S", "cont_upstream_to_cds_3", {"upstream": 0.5, "downstream": 0.3, "cds": 0.2}, "upstream_only", "final"),
    Run("2.4·S", "cont_upstream_to_downstream_1", {"upstream": 0.5, "downstream": 0.5}, "upstream_only", "final"),
    Run("2.1.1·S", "cont_upstream_to_cds_2.2", {"downstream": 0.8, "upstream": 0.1, "cds": 0.1}, "cont_upstream_to_cds_2", "final"),
    # Trees 3-6 — leaf roots (region-only baselines, then the two zoonomia bases).
    # cds_only crashed at ~70%; included unflagged as the C-only baseline, with its
    # own-token count scaled by run_progress in the figure (it never finished).
    Run("3·L", "cds_only", {"cds": 1.0}, None, "root"),
    Run("4·S", "downstream_only", {"downstream": 1.0}, None, "root"),
    Run("5·L", "exp135-zoonomia-m1",
        {"cds": _FIFTH, "upstream": _FIFTH, "downstream": _FIFTH, "ncrna_exon": _FIFTH, "ccre_non_promoter": _FIFTH},
        None, "root"),
    Run("6·L", "exp135-zoonomia-m3",
        {"cds": 0.1875, "upstream": 0.25, "downstream": 0.1875, "ncrna_exon": 0.1875, "ccre_non_promoter": 0.1875},
        None, "root"),
)

BY_MIX: dict[str, Run] = {r.mix: r for r in LINEAGE}


def children_of(mix: str) -> list[Run]:
    """Direct children of `mix`, in LINEAGE (left→right) order."""
    return [r for r in LINEAGE if r.parent == mix]


def _branch_fraction(run: Run) -> float:
    return COOLDOWN_KEEP_FRACTION if run.branch == "pre_cooldown" else 1.0


def inherited_components(mix: str, own_tokens: dict[str, float]) -> dict[str, float]:
    """Per-component tokens `mix` inherited at warm-start (everything its parent
    accumulated up to the branch point). `own_tokens` maps mix → its own token tag.
    """
    run = BY_MIX[mix]
    if run.parent is None:
        return {}
    parent = BY_MIX[run.parent]
    comp = dict(inherited_components(run.parent, own_tokens))  # grandparent+ at 100%
    f = _branch_fraction(run)
    parent_own = own_tokens[run.parent]
    for region, w in parent.weights.items():
        if w > 0:
            comp[region] = comp.get(region, 0.0) + f * parent_own * w
    return comp


def cumulative_components(mix: str, own_tokens: dict[str, float]) -> dict[str, float]:
    """Per-component cumulative tokens over the full lineage (inherited + own)."""
    run = BY_MIX[mix]
    comp = dict(inherited_components(mix, own_tokens))
    own = own_tokens[mix]
    for region, w in run.weights.items():
        if w > 0:
            comp[region] = comp.get(region, 0.0) + own * w
    return comp


def cumulative_total(mix: str, own_tokens: dict[str, float]) -> float:
    """Total cumulative tokens over the lineage (sum of components)."""
    return sum(cumulative_components(mix, own_tokens).values())


def composite_score(row) -> float:
    """Mean of the 6 VEP-subset AUPRCs (the composite 6-task score)."""
    cols = [f"lm_eval/traitgym_mendelian_v2_255/{s}/auprc" for s in COMPOSITE_SUBSETS]
    return sum(float(row[c]) for c in cols) / len(cols)


def format_mixture(weights: dict[str, float]) -> str:
    """Compact mixture label: uniform mixes as 'CUD ⅓'; else 'U90 C5 D5'."""
    active = [(r, w) for r, w in weights.items() if w > 0]
    active.sort(key=lambda t: (-t[1], REGION_ORDER.index(t[0])))
    rounded = {round(w, 3) for _, w in active}
    if len(active) > 1 and len(rounded) == 1:
        letters = "".join(REGION_LETTER[r] for r, _ in sorted(active, key=lambda t: REGION_ORDER.index(t[0])))
        frac = {3: "⅓", 5: "⅕"}.get(len(active), f"1/{len(active)}")
        return f"{letters} {frac}"
    return " ".join(f"{REGION_LETTER[r]}{round(w * 100)}" for r, w in active)


def format_tokens(n: float) -> str:
    """Human token count, e.g. 5.2e9 -> '5.2B'."""
    if n >= 1e9:
        return f"{n / 1e9:.1f}B"
    return f"{n / 1e6:.0f}M"
