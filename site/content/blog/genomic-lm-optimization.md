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

Optimization of genomic language models (gLMs) has historically involved a lot of focus on model architecture. At a high level, the field has explored architecture ideas borrowed from language and vision,[^glm-architecture] methods for making raw DNA usable at long context,[^glm-tokenization] and genomics-specific priors that encode biological symmetries, structure, or evolution.[^glm-biology] Our results here push against the idea that these inductive biases are necessary for human variant effect prediction (VEP), arguably the most important near-term use case for gLMs. In the zero-shot setting, a standard decoder-only autoregressive model can surpass Evo 2 40B when it is paired with focused data curation, the scaling practices we used previously in [Delphi](https://openathena.ai/blog/delphi/), and a set of less-principled ad-hoc runs where the cleaner recipe stopped being enough. The final model does so with 1.8% as many training tokens (166B vs. 9.3T) and roughly 0.05% as many FLOPs (1.1e21 vs. 2.25e24).

### Why VEP eval?

VEP is arguably the most important application of gLMs. A useful VEP model can help scale clinical interpretation for rare disease, hereditary cancer, and variants of uncertain significance.[^vep-clinical] It can also help connect genetic association signals to disease mechanisms, target selection, and causal-variant prioritization in GWAS fine-mapping.[^vep-therapeutic] The same kind of evidence is relevant to clinical trial design when genetics can inform patient stratification, enrollment criteria, or mechanism-based cohort definition.[^vep-trials] Together, these are commonly used levers for improving the efficiency of pharmaceutical development, including target selection, indication selection, and clinical trial design. VEP is also one of the few evaluations backed by decades of costly clinical genetics curation, with resources such as ClinVar and OMIM providing a level of human variant evidence that has no real analogue in other species.[^human-variant-curation] That combination makes it a consequential test of whether a gLM has learned sequence constraints that actually matter for human biology. If a model has learned useful sequence-level constraints from DNA alone, it should help rank variants in places where direct experimental evidence is weak or nonexistent.

### Why Evo 2 40B baseline?

Evo 2 40B is the hardest relevant baseline among unsupervised, single-sequence DNA models. Stronger models exist for some variant-effect settings, but they usually change the problem. AlphaGenome uses supervised functional genomics signals. GPN-Star uses alignments, species trees, and a bespoke evolutionary architecture. Evo 2 40B is different. It is a very large DNA-only model, trained from sequence alone, with broad zero-shot VEP results and an unusually large training budget. Its reported 2.25e24 training FLOPs are not just large for biology. They sit in the same range as major open LLM generations,[^evo2-llm-compute] just above Qwen2.5-14B and below Qwen2.5-32B, and roughly between DeepSeek-V2 and DeepSeek-V3 under active-parameter MoE accounting. That makes it the right baseline for asking whether a much simpler single-sequence gLM can compete.

### Why Decoder-Only Autoregressive Models?

A decoder-only autoregressive Transformer is the simplest serious test of whether architecture is actually the bottleneck. It is not biologically elegant, but it is standard, scalable, and easy to run across existing training and inference stacks. There is also more precedent for this plain modeling approach than the architecture-heavy narrative suggests.[^causal-glm-precedent] Carbon is the closest recent example. Carbon-3B is a stock LlamaForCausalLM-style decoder with 6-mer DNA tokens, long-context training, and a cross-entropy-to-FNS objective schedule. Its public zero-shot VEP table scores variants with likelihood-based sequence scoring across BRCA2, TraitGym Mendelian, ClinVar coding, and ClinVar noncoding. Carbon-3B beats Evo2-7B on BRCA2 and ClinVar noncoding, but trails on ClinVar coding and TraitGym Mendelian.[^carbon-eval] GENERATOR-v2 is another decoder-style precedent in the same comparison table, where it beats Evo2-7B on ClinVar noncoding but not on the other listed human VEP tasks. With the right data, transferable hyperparameters, and targeted ad-hoc mixture experiments, that turns out to be enough. The practical upside is large. Smaller standard models are cheaper to serve, easier to reproduce, easier to move across hardware, and less dependent on custom kernels or model-specific infrastructure.

[^glm-architecture]: Examples include long-convolution or hybrid long-context models such as [HyenaDNA](https://arxiv.org/abs/2306.15794) and [Evo 2](https://doi.org/10.1101/2025.02.18.638918); U-Net-like sequence-function models such as [NTv3](https://doi.org/10.64898/2025.12.22.695963); bidirectional models such as [DNABERT-2](https://arxiv.org/abs/2306.15006), [GenSLM](https://www.biorxiv.org/content/10.1101/2023.06.12.544594v3.full.pdf), [Caduceus](https://arxiv.org/abs/2403.03234), [PlantCAD2](https://doi.org/10.1101/2025.08.27.672609), and [TrinityDNA](https://arxiv.org/abs/2507.19229); state-space or hybrid state-space models such as [HybriDNA](https://arxiv.org/abs/2502.10807), [Caduceus](https://arxiv.org/abs/2403.03234), and [PlantCAD2](https://doi.org/10.1101/2025.08.27.672609); and early or less-established sparse-expert models such as [JanusDNA](https://arxiv.org/abs/2505.17257), [PlantBiMoE](https://arxiv.org/abs/2512.07113), and [MxDNA](https://arxiv.org/abs/2412.13716).

[^glm-tokenization]: Examples include learned or tokenizer-free approaches such as [dnaHNet](https://arxiv.org/abs/2602.10603) and [DNACHUNKER](https://arxiv.org/abs/2601.03019), multi-scale Transformers such as [MegaDNA](https://www.biorxiv.org/content/10.1101/2023.12.18.572218v3.full), and multi-scale attention in [TrinityDNA](https://arxiv.org/abs/2507.19229).

[^glm-biology]: Examples include reverse-complement equivariance in [Caduceus](https://arxiv.org/abs/2403.03234), double-helix groove fusion in [TrinityDNA](https://arxiv.org/abs/2507.19229), genomic loss weighting in [Evo 2](https://doi.org/10.1101/2025.02.18.638918) and [GPN](https://www.pnas.org/doi/10.1073/pnas.2311219120), factorized nucleotide supervision in [GENERATOR-v2](https://doi.org/10.64898/2026.01.27.702015) and related objective design in [Carbon](https://doi.org/10.64898/2026.05.22.727119). Outside unsupervised, single-sequence DNA language modeling, related architectural examples include the convolutional U-Net Transformer plus pairwise contact-map model in [AlphaGenome](https://doi.org/10.1101/2025.06.25.661532) and sequence-alignment plus phylogeny-aware attention in [GPN-Star](https://doi.org/10.1101/2025.09.21.677619).

[^vep-clinical]: Examples include zero-shot or disease-focused variant interpretation results in [Evo 2](https://doi.org/10.1101/2025.02.18.638918), [GPN-Star](https://doi.org/10.1101/2025.09.21.677619), [Carbon](https://doi.org/10.64898/2026.05.22.727119), [EnTao-GPM](https://arxiv.org/abs/2507.21706), and [DYNA](https://arxiv.org/abs/2406.00164).

[^vep-therapeutic]: Examples include fine-mapped GWAS and broader human-genetics results in [GPN-Star](https://doi.org/10.1101/2025.09.21.677619), regulatory variant-effect prediction in [AlphaGenome](https://doi.org/10.1101/2025.06.25.661532) and [ChromBPNet](https://www.biorxiv.org/content/10.1101/2024.12.25.630221v2), and the broader observation that human genetic evidence can support target-disease hypotheses in drug discovery in [Nelson et al.](https://doi.org/10.1038/ng.3314).

[^vep-trials]: Genetics-informed trial design is downstream of variant interpretation rather than a single canonical gLM benchmark. Relevant examples include disease-specific variant models such as [DYNA](https://arxiv.org/abs/2406.00164), germline pathogenicity models such as [EnTao-GPM](https://arxiv.org/abs/2507.21706), and risk-score enrichment designs such as [CADEN](https://arxiv.org/abs/2111.02299).

[^human-variant-curation]: [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/intro/) archives submitted reports relating human genomic variation to disease, cancer, drug response, and supporting evidence; [OMIM](https://doi.org/10.1093/nar/gku1205) is a curated catalog of human genes, genetic disorders, and gene-phenotype relationships. These resources are imperfect and clinically ascertained, but the depth of human disease curation behind them is exactly what makes human VEP a more meaningful test than most non-human variant benchmarks.

[^evo2-llm-compute]: Other over/under examples give the same intuition. The [AI2 OLMo 2 32B model card](https://huggingface.co/allenai/OLMo-2-0325-32B) places Evo 2 40B above Gemma 2 27B, OLMo 2 32B, and Llama 3.1 8B. A dense-accounting estimate from the [Llama 3.1 model card](https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/MODEL_CARD.md) places it well below Llama 3.1 70B. The exact accounting differs across dense and MoE models, but the comparison is still useful: Evo 2 40B was trained at the scale of a serious modern LLM generation, not at the scale of a typical biology model.

[^causal-glm-precedent]: Decoder-only or otherwise causal genomic models include [GenSLM](https://pmc.ncbi.nlm.nih.gov/articles/PMC9709791/), [DNAGPT](https://arxiv.org/abs/2307.05628), [METAGENE-1](https://arxiv.org/abs/2501.02045), [GENERATOR](https://arxiv.org/abs/2502.07272), [GENERATOR-v2](https://doi.org/10.64898/2026.01.27.702015), [Gene42](https://arxiv.org/abs/2503.16565), and [Carbon](https://doi.org/10.64898/2026.05.22.727119). Carbon is the closest recent precedent for the argument here because it combines a standard decoder-only implementation with modern long-context DNA training and explicit zero-shot VEP comparisons to Evo2-7B.

[^carbon-eval]: The [Carbon-3B model card](https://huggingface.co/HuggingFaceBio/Carbon-3B) describes Carbon-3B as a 3B-parameter decoder-only autoregressive genomic model, implemented as a stock `LlamaForCausalLM`, with non-overlapping 6-mer DNA tokenization, native 32,768-token context, YaRN extension to 65,536 tokens, and a cross-entropy-to-factorized-nucleotide-supervision training schedule. The same card reports likelihood-based scoring for perturbation and VEP tasks and lists headline zero-shot scores of Carbon-3B versus Evo2-7B as 84.63 versus 83.52 on BRCA2, 91.14 versus 89.79 on ClinVar noncoding, 92.89 versus 93.33 on ClinVar coding, and 33.65 versus 37.78 on TraitGym Mendelian. GENERATOR-v2-3B appears in the same table with 90.13 on ClinVar noncoding, but trails Evo2-7B on BRCA2, ClinVar coding, and TraitGym Mendelian.

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
