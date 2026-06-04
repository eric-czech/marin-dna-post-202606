Title: Genomic Language Model Optimization
Subtitle: Pretraining near-SOTA, single-sequence gLMs on Marin with hyperparameter transfer, scaling law and mixture experiments.

## Intro

TBD

## Hyperparameter Transfer

- Cite Delphi post
- Explain proportional data mix
- Explain reference Vizier sweep
- Explain transfer validation
  - Show:
    - Figure 1 (LR transfer)
    - Figure 2 (beta2 + epsilon)
  - LR is far more sensitive
    - Explain what this means for trying to run experiments w/o scaling LR based on tokens
  - Show Figure 3 (transfer by region)

## Parameter Scaling

- Show Figure 4
- Loss scaling is smooth and fits to standard Kaplan laws well

## Downstream Performance

- Show Figure 5
  - As expected, parameter scaling does yield monotonic improvements
- Show Figure 6
  - Loss correlation is weak
- Show figures/appendix/loss_vs_traitgym_curves.svg
  - Notably, VEP performance degrades at the largest model scales with more tokens
- Show figures/appendix/loss_vs_traitgym_correlation.svg
  - However, we can see that VEP performance scales more monotonically within a range of model sizes

 ## Mixture Experiments

 - 1B is on the upper end of model scales with higher VEP monotonicity
 - We continue pretraining on more tokens at that scale with different mixtures
   - These experiments rely on hyper transfer to new token horizons
 - Beginning with a checkpoint trained on a uniform mixture, we test shifts in mixture weight to compensate for gaps in specific VEP tasks 
   - We focus on improving promoter and 5' UTR performance by shifting weights to upstream sequences
   - Show Figure 7
  - Improvements from deviating off of uniform mixtures are minimal
- For this reason, we continue pretraining on animal data while preparing enhancer data 
  - Training continues to ~104B tokens before mixing in new data
  - After ~62B tokens, performance improves drastically on distal tasks
- Our net result is a PoC for a 1B model on par with Evo 2 40B after training on just 1.8% as many tokens (166B vs 9.3T) and ~0.05% as many FLOPs (1.1e21 vs 2.25e24)
