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

Optimization of genomic language models (gLMs) has historically involved a lot of focus on model architecture. At a high level, the field has explored architecture ideas borrowed from language and vision, methods for making raw DNA usable at long context, and genomics-specific priors that encode biological symmetries, structure, or evolution.[^glm-architecture][^glm-tokenization][^glm-biology] Our result pushes against the idea that these inductive biases are necessary for the most important near-term gLM use case. For zero-shot human variant effect prediction (VEP), a standard decoder-only autoregressive model can surpass Evo 2 40B when it is paired with focused data curation, the scaling practices we used in [Delphi](https://openathena.ai/blog/delphi/), and a set of less-principled ad-hoc runs where the cleaner recipe stopped being enough. The final model reaches this result with 1.8% as many training tokens (166B vs. 9.3T) and roughly 0.05% as many FLOPs (1.1e21 vs. 2.25e24).

### Why VEP?

VEP is where gLMs are most likely to matter first. A useful VEP model helps decide which genetic variants deserve attention in rare-disease diagnosis, hereditary cancer interpretation, VUS triage, fine-mapped GWAS follow-up, target selection, patient stratification, and trial enrollment. These are already high-value decisions across medicine and drug discovery, and they are often limited by sparse labels, incomplete assays, and uneven functional annotation. That makes VEP a natural test for unsupervised genomic modeling. If a model has learned useful sequence-level constraints from DNA alone, it should help rank variants in places where direct experimental evidence is thin.

### Why Evo 2 40B?

Evo 2 40B is the hardest relevant baseline among unsupervised, single-sequence DNA models. Stronger models exist for some variant-effect settings, but they usually change the problem. AlphaGenome uses supervised functional genomics signals. GPN-Star uses alignments, species trees, and a bespoke evolutionary architecture. Evo 2 40B is different. It is a very large DNA-only model, trained from sequence alone, with broad zero-shot VEP results and an unusually large training budget. That makes it the right baseline for asking whether a much simpler single-sequence gLM can compete.

### Why Decoder-Only Autoregressive Models?

A decoder-only autoregressive Transformer is the simplest serious test of whether architecture is actually the bottleneck. It is not biologically elegant, but it is standard, scalable, and easy to run across existing training and inference stacks. With the right data, transferable hyperparameters, and targeted ad-hoc mixture experiments, that turns out to be enough. The practical upside is large. Smaller standard models are cheaper to serve, easier to reproduce, easier to move across hardware, and less dependent on custom kernels or model-specific infrastructure.

[^glm-architecture]: Examples include long-convolution or hybrid long-context models such as [HyenaDNA](https://arxiv.org/abs/2306.15794) and [Evo 2](https://doi.org/10.1101/2025.02.18.638918); U-Net-like sequence-function models such as [NTv3](https://doi.org/10.64898/2025.12.22.695963); bidirectional models such as [DNABERT-2](https://arxiv.org/abs/2306.15006), [GenSLM](https://www.biorxiv.org/content/10.1101/2023.06.12.544594v3.full.pdf), [Caduceus](https://arxiv.org/abs/2403.03234), [PlantCAD2](https://doi.org/10.1101/2025.08.27.672609), and [TrinityDNA](https://arxiv.org/abs/2507.19229); state-space or hybrid state-space models such as [HybriDNA](https://arxiv.org/abs/2502.10807), [Caduceus](https://arxiv.org/abs/2403.03234), and [PlantCAD2](https://doi.org/10.1101/2025.08.27.672609); and early or less-established sparse-expert models such as [JanusDNA](https://arxiv.org/abs/2505.17257), [PlantBiMoE](https://arxiv.org/abs/2512.07113), and [MxDNA](https://arxiv.org/abs/2412.13716).

[^glm-tokenization]: Examples include learned or tokenizer-free approaches such as [dnaHNet](https://arxiv.org/abs/2602.10603) and [DNACHUNKER](https://arxiv.org/abs/2601.03019), multi-scale Transformers such as [MegaDNA](https://www.biorxiv.org/content/10.1101/2023.12.18.572218v3.full), and multi-scale attention in [TrinityDNA](https://arxiv.org/abs/2507.19229).

[^glm-biology]: Examples include reverse-complement equivariance in [Caduceus](https://arxiv.org/abs/2403.03234), double-helix groove fusion in [TrinityDNA](https://arxiv.org/abs/2507.19229), genomic loss weighting in [Evo 2](https://doi.org/10.1101/2025.02.18.638918) and [GPN](https://www.pnas.org/doi/10.1073/pnas.2311219120), factorized nucleotide supervision in [GENERATOR-v2](https://doi.org/10.64898/2026.01.27.702015) and related objective design in [Carbon](https://doi.org/10.64898/2026.05.22.727119). Outside unsupervised, single-sequence DNA language modeling, related architectural examples include the convolutional U-Net Transformer plus pairwise contact-map model in [AlphaGenome](https://doi.org/10.1101/2025.06.25.661532) and sequence-alignment plus phylogeny-aware attention in [GPN-Star](https://doi.org/10.1101/2025.09.21.677619).

## Results

### Hyperparameter Transfer

- Cite the Delphi post.
- Proportional data mix: spans 3 genomic regions (CDS, upstream, downstream) — ~331M training examples / ~85B tokens from 366,411 RefSeq accessions across ~500 species.
  - The proportional mix avoids conflation with epoching effects — each region is cycled only once.
  - We do not yet have a mature, data-constrained hyperparameter-transfer framework.
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

### Parameter Scaling

- 8 model sizes (46M–4B params) at ~84B tokens each (~4.3e21 FLOPs across the sweep).

![Loss scaling across model sizes with Kaplan power-law fits](/assets/images/blog/genomic-lm-optimization/figure4_loss_scaling.svg)

**Figure 4:** Loss scaling across 8 model sizes (46M–4B params), with Kaplan power-law fits.

- Loss scaling is smooth and fits standard Kaplan laws well.

### Downstream Performance

- As expected from prior art, parameter scaling does not yield monotonic improvements despite the tuning.

![Composite VEP AUPRC vs parameter count](/assets/images/blog/genomic-lm-optimization/figure5_params_vs_vep_auprc.svg)

**Figure 5:** Composite VEP AUPRC vs parameter count.

- The loss correlation is weak.

![Composite VEP AUPRC vs validation loss](/assets/images/blog/genomic-lm-optimization/figure6_loss_vs_vep_auprc.svg)

**Figure 6:** Composite VEP AUPRC vs validation loss.

- Notably, VEP performance degrades at the largest model scales with more tokens.

![VEP AUPRC training curves by model scale](/assets/images/blog/genomic-lm-optimization/figure7_loss_vs_traitgym_curves.svg)

**Figure 7:** VEP AUPRC training curves by model scale.

- However, VEP performance scales more monotonically within a range of model sizes.

![Loss vs VEP AUPRC correlation within model-size ranges](/assets/images/blog/genomic-lm-optimization/figure8_loss_vs_traitgym_correlation.svg)

**Figure 8:** Loss vs VEP AUPRC correlation within model-size ranges.

### Mixture Experiments

- To further optimize our models, we move away from theoretically-grounded, compute-constrained methods.
  - Instead, we focus on the mixture constituents — epoching them freely — and how far they can be modified in-flight to compensate for observed performance gaps (YOLO).
- This still relies on two key results from the parameter-scaling sweep:
  - Hyperparameter-transfer scaling heuristics, to configure runs with very different token horizons.
  - A 1B target scale — the largest model that still exhibited high VEP monotonicity.
- We begin by training at 1B params on a uniform mixture of the same 3-region animal sequences used previously.
  - By ~50B tokens, this saturated on upstream tasks (promoters and 5' UTRs) at significantly lower levels than models trained on upstream sequence alone.
  - We then test shifts in mixture weights to see whether upstream task performance can be improved without sacrificing the others.

![Composite VEP AUPRC vs upstream mixture proportion](/assets/images/blog/genomic-lm-optimization/figure9_upstream_mix_auprc.svg)

**Figure 9:** Composite VEP AUPRC vs upstream mixture proportion, against the uniform baseline (dotted).

- Upstream task gains are easily undone by performance lost on other tasks.
  - Similar experiments starting from upstream-only models or proportionally-weighted checkpoints likewise yielded no clear net wins.
- Conclusion: improving zero-shot performance mid-flight is **not** really possible by re-weighting **existing** mixture components.
- As an alternative, we instead mix in new, distal sequence data — largely mammalian enhancer sequences — with uniform weighting.
  - This expands the mixture pool from 3 genomic regions (CDS, upstream, downstream) to 5 (+ ncRNA exons and enhancers).
  - Surprisingly, this improves upstream task performance significantly (promoter VEP 30% → 40%) and very drastically improves distal task performance (ncRNA exon variants 19% → 65%, enhancer variants 14% → 33%), while mostly holding performance on other tasks fixed.
  - Our best recipe so far trains on a uniformly-weighted, 3-region mixture of sequence data proximal to genes (~104B tokens), followed by continued pretraining on a uniformly-weighted, 5-region mixture expanded to include distal sequences (~62B tokens).
    - This outperforms de novo training on the 5-region mixture.

![VEP AUPRC trajectories by mixture lineage](/assets/images/blog/genomic-lm-optimization/figure10_lineage_vep_trajectory.svg)

**Figure 10:** VEP AUPRC trajectories vs training tokens for three model-mixture lineages (macro average highlighted, top-left). The dashed line marks where the best recipe (m5.1) shifts from a 3-region to a 5-region mixture — the inflection in the distal and non-coding-exon panels.

- Conclusion: improving zero-shot performance mid-flight **is** possible by adding **new**, uniformly-weighted mixture components.

## Conclusion

- Our net result is a PoC for a 1B model on par with Evo 2 40B after training on just 1.8% as many tokens (166B vs 9.3T) and ~0.05% as many FLOPs (1.1e21 vs 2.25e24).

![Mendelian VEP benchmark AUPRC heatmap across models](/assets/images/blog/genomic-lm-optimization/figure11_leaderboard_heatmap.svg)

**Figure 11:** Mendelian VEP benchmark — AUPRC (%) across models, with the Macro Avg column highlighted.

- This model resulted from a messy, ad-hoc process aided in unanticipated ways by the hyperparameter-transfer, scaling, and mixture tools within Marin.
  - Many less successful attempts are not mentioned here but are documented at [Open-Athena/marin-dna](https://github.com/Open-Athena/marin-dna).
- Ongoing work will hopefully yield a more consistent, effective training strategy.
