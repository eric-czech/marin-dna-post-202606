---
title: "Genomic Language Model Optimization"
slug: "genomic-lm-optimization"
author: "TODO"
date: 2026-06-04
published: true
math: false
toc: true
tags:
  - Marin
summary: "How Marin can be used to train single-sequence, vanilla Transformer gLMs comparable to Evo 2 40B with ~1,980× fewer FLOPs, via hyperparameter transfer, scaling laws, and training-mixture experiments."
---

<style>
/* Math labels in the figures are positioned per-glyph from DejaVu Sans metrics,
   so they're left in DejaVu (the rest of the labels inherit the page font). Embed
   DejaVu so those positions render correctly instead of mis-spacing on a fallback. */
@font-face {
  font-family: 'DejaVu Sans';
  src: url('assets/fonts/DejaVuSans.woff2') format('woff2');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}
.blog-post-content figure img,
.blog-post-content figure svg.figure-svg {
  background: #ece3d5;
  padding: 1rem 1.25rem;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(31, 30, 27, 0.10);
}
/* Inlined matplotlib figures: the viewBox carries the aspect ratio, so let the
   SVG fill the column and scale its height automatically. Authored with live
   <text> and currentColor (see site/build.py + utils.figure_theme), so labels
   render in the page font and follow the page ink. */
.blog-post-content figure svg.figure-svg {
  display: block;
  width: 100%;
  height: auto;
  box-sizing: border-box;
}
/* Nested lists inherit ul's 1rem margin-bottom, which stacks with the parent
   <li>'s margin to leave an oversized gap before the next top-level bullet.
   Zero it so nested bullets sit flush with the following item. */
.blog-post-content li > ul,
.blog-post-content li > ol {
  margin-bottom: 0;
}
</style>

*Draft — prose is intentionally skeletal pending a full write-up.*

How Marin can be used to train single-sequence, vanilla Transformer gLMs comparable to Evo 2 40B with ~1,980× fewer FLOPs. Covers hyperparameter transfer, scaling-law, and training-mixture experiments.

## Introduction

- This post is about how novel data curation strategies (from Gonzalo) can be paired with standard LLM training infrastructure and methods to build highly competitive gLMs.
- This post is NOT about how to do so systematically; it is a patchwork of experiments that connected in unexpected ways to prove something difficult is possible.

## Hyperparameter Transfer

- Cite the Delphi post.
- Proportional data mix: spans 3 genomic regions (CDS, upstream, downstream) — ~331M training examples / ~85B tokens from 366,411 RefSeq accessions across ~500 species.
- Reference Vizier sweep: ~25M params, 2.5B tokens, 16k batch (~4e17 FLOPs/run).
- Transfer validation: 10B tokens, 4k batch (~6.8e19 FLOPs/run); 76 runs across the 255M / 476M / 1B scales (~2.9e21 FLOPs total).

![Learning-rate transfer across model scales](/assets/images/blog/genomic-lm-optimization/figure1_lr_transfer.svg)

**Figure 1:** Learning-rate (LR) transfer across the 255M, 476M, and 1B validation scales.

![Adam beta2 and epsilon transfer across model scales](/assets/images/blog/genomic-lm-optimization/figure2_beta2_epsilon_transfer.svg)

**Figure 2:** Adam β₂ and ε transfer across the same scales.

- LR is far more sensitive than β₂ or ε.
  - This matters when running experiments without re-scaling LR to the token horizon.

<details>
<summary>Transfer validation by region (Figure 3)</summary>

![Hyperparameter transfer validated per genomic region](/assets/images/blog/genomic-lm-optimization/figure3_region_hyper_transfer.svg)

**Figure 3:** Hyperparameter transfer validated separately for each genomic region (CDS, upstream, downstream).

</details>

## Parameter Scaling

- 8 model sizes (46M–4B params) at ~84B tokens each (~4.3e21 FLOPs across the sweep).

![Loss scaling across model sizes with Kaplan power-law fits](/assets/images/blog/genomic-lm-optimization/figure4_loss_scaling.svg)

**Figure 4:** Loss scaling across 8 model sizes (46M–4B params), with Kaplan power-law fits.

- Loss scaling is smooth and fits standard Kaplan laws well.

## Downstream Performance

- As expected from prior art, parameter scaling does not yield monotonic improvements despite the tuning.

![Composite VEP AUPRC vs parameter count](/assets/images/blog/genomic-lm-optimization/figure5_params_vs_vep_auprc.svg)

**Figure 5:** Composite VEP AUPRC vs parameter count.

- The loss correlation is weak.

![Composite VEP AUPRC vs validation loss](/assets/images/blog/genomic-lm-optimization/figure6_loss_vs_vep_auprc.svg)

**Figure 6:** Composite VEP AUPRC vs validation loss.

- Notably, VEP performance degrades at the largest model scales with more tokens.

![VEP AUPRC training curves by model scale](/assets/images/blog/genomic-lm-optimization/appendix/loss_vs_traitgym_curves.svg)

**Figure A1:** VEP AUPRC training curves by model scale (appendix).

- However, VEP performance scales more monotonically within a range of model sizes.

![Loss vs VEP AUPRC correlation within model-size ranges](/assets/images/blog/genomic-lm-optimization/appendix/loss_vs_traitgym_correlation.svg)

**Figure A2:** Loss vs VEP AUPRC correlation within model-size ranges (appendix).

## Mixture Experiments

- 1B is on the upper end of model scales with higher VEP monotonicity.
- We continue pretraining on more tokens at that scale with different mixtures.
  - These experiments rely on hyperparameter transfer to new token horizons.
- Beginning with a checkpoint trained on a uniform mixture, we test shifts in mixture weight to compensate for gaps in specific VEP tasks.
  - We focus on improving promoter and 5' UTR performance by shifting weights to upstream sequences.

![Composite VEP AUPRC vs upstream mixture proportion](/assets/images/blog/genomic-lm-optimization/figure7_upstream_mix_auprc.svg)

**Figure 7:** Composite VEP AUPRC vs upstream mixture proportion, against the uniform baseline (dotted).

- Improvements from deviating off of uniform mixtures are minimal.
- For this reason, we continue pretraining on animal data while preparing mammalian enhancer data.
  - Training continues to ~104B tokens before mixing in new data.
  - After ~62B tokens, performance improves drastically on distal tasks.

## Conclusion

- Our net result is a PoC for a 1B model on par with Evo 2 40B after training on just 1.8% as many tokens (166B vs 9.3T) and ~0.05% as many FLOPs (1.1e21 vs 2.25e24).

![Mendelian VEP benchmark AUPRC heatmap across models](/assets/images/blog/genomic-lm-optimization/figure8_leaderboard_heatmap.svg)

**Figure 8:** Mendelian VEP benchmark — AUPRC (%) across models, with the Macro Avg column highlighted.

- This model resulted from a messy, ad-hoc process aided in unanticipated ways by the hyperparameter-transfer, scaling, and mixture tools within Marin.
  - Many less successful attempts are not mentioned here but are documented at [Open-Athena/marin-dna](https://github.com/Open-Athena/marin-dna).
- Ongoing work will hopefully yield a more consistent, effective training strategy.
