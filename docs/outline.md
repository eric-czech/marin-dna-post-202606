Title: Genomic Language Model Optimization
Description: How Marin can be used to train single-sequence, vanilla Transfer gLMs comparable to Evo2 40B with 1,980x fewer FLOPS. Covers hyperparameter transfer, scaling law and training mixture experiments.

## Introduction

- This post is about how novel data curation strategies (from Gonzalo) can be paired with standard LLM training infrastructure and methods to build highly competitive gLMs
- This post is NOT about how to do so systematically; it is a patchwork of experiments that connected in unexpected ways to prove something difficult is possible

## Hyperparameter Transfer

- Cite Delphi post
- Explain proportional data mix
  - Spans 3 genomic regions (CDS, upstream, downstream): ~331M training examples / ~85B tokens from 366,411 RefSeq accessions across ~500 species
- Explain reference Vizier sweep
  - ~25M params, 2.5B tokens, 16k batch (~4e17 FLOPs/run)
- Explain transfer validation
  - 10B tokens, 4k batch (~6.8e19 FLOPs/run); 76 runs across 255M/476M/1B scales (~2.9e21 FLOPs total)
  - Show Figure 1 (LR transfer) and Figure 2 (beta2 + epsilon)
  - LR is far more sensitive
    - Explain what this means for trying to run experiments w/o scaling LR based on tokens
  - Show Figure 3 (validation by region)

## Parameter Scaling

- 8 model sizes (46M–4B params) at ~84B tokens each (~4.3e21 FLOPs across the sweep)
  - Show Figure 4
- Loss scaling is smooth and fits to standard Kaplan laws well

## Downstream Performance

- As expected from prior art, parameter scaling does not yield monotonic improvements despite the tuning and scaling law results
  - Show Figure 5
- Loss correlation is weak
  - Show Figure 6
- Notably, VEP performance degrades at the largest model scales with more tokens
  - Show figures/appendix/loss_vs_traitgym_curves.svg
- However, we can see that VEP performance scales more monotonically within a range of model sizes
  - Show figures/appendix/loss_vs_traitgym_correlation.svg

 ## Mixture Experiments

 - 1B is on the upper end of model scales with higher VEP monotonicity
 - We continue pretraining on more tokens at that scale with different mixtures
   - These experiments rely on hyper transfer to new token horizons
 - Beginning with a checkpoint trained on a uniform mixture, we test shifts in mixture weight to compensate for gaps in specific VEP tasks 
   - We focus on improving promoter and 5' UTR performance by shifting weights to upstream sequences
   - Show Figure 7
  - Improvements from deviating off of uniform mixtures are minimal
- For this reason, we continue pretraining on animal data while preparing mamallian enhancer data 
  - Training continues to ~104B tokens before mixing in new data
  - After ~62B tokens, performance improves drastically on distal tasks

## Conclusion

- Our net result is a PoC for a 1B model on par with Evo 2 40B after training on just 1.8% as many tokens (166B vs 9.3T) and ~0.05% as many FLOPs (1.1e21 vs 2.25e24)
  - Show Figure 8
- This model resulted from a messy, ad-hoc process aided in unanticipated ways by hyperparameter transfer, scaling and mixture tools within Marin
  - Many less successful attempts are not mentioned here but documented in https://github.com/Open-Athena/marin-dna
- Ongoing work will hopefully yield a more consistent, effective training strategy