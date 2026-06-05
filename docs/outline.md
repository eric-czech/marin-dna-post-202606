Title: Genomic Language Model Optimization
Description: How Marin can be used to train single-sequence, vanilla Transformer gLMs comparable to Evo2 40B with 1,980x fewer FLOPS. Covers hyperparameter transfer, scaling law and training mixture experiments.

## Introduction

- This post is about how novel data curation strategies (from Gonzalo) can be paired with standard LLM training infrastructure and methods to build highly competitive gLMs
- This post is NOT about how to do so systematically; it is a patchwork of experiments that connected in unexpected ways to prove something difficult is at least possible

## Hyperparameter Transfer

- Cite Delphi post
- Explain proportional data mix
  - Spans 3 genomic regions (CDS, upstream, downstream): ~331M training examples / ~85B tokens from 366,411 RefSeq accessions across ~500 species
  - Proportional mix avoids conflation with epoching effects; each region is cycled only once
  - We do not yet have a mature, data-constrained hyperparameter transfer framework
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
  - Show Figure 7
- However, we can see that VEP performance scales more monotonically within a range of model sizes
  - Show Figure 8

 ## Mixture Experiments

- In an effort to further optimize our models, we move away from theoretically-grounded compute-constrained methods
  - Instead, we focus on mixture constituents (epoching them freely) and the extent to which they can be modified in-flight to compensate for observed performance gaps (YOLO)
- This still relies on two key results from the parameter scaling sweep:
  - Hyperparameter transfer scaling heuristics to configure training runs with very different token horizons
  - 1B target model scale since it was the largest model that still exhibited high VEP monotonicity
- We begin by training at 1B params on a uniform mixture of the same 3-region, animal sequences used previously
  - By ~50B tokens, this demonstrated saturation on upstream tasks (promoters and 5' UTRs) at significantly lower levels than models trained on upstream sequence alone
  - We then test shifts in mixture weights to identify whether or not upstream task performance can be improved without sacrificing performance on others
  - Show Figure 9
  - Upstream task gains are easily undone by performance lost on other tasks 
    - Similar experiments starting from models trained only on upstream data or from proportionally weighted checkpoints instead yielded no clear net-wins
  - Conclusion: improving zero-shot performance mid-flight is not really possible with non-uniform weighting of **existing** mixture components
- As an alternative strategy, we instead mix in new, distal sequence data largely from mammalian enhancer sequences with uniform weighting
  - This increases our mixture pool from 3 genomic regions (CDS, upstream, downstream) to 5 (+ncRNA exons and enhancers)
  - Surprisingly, this improves upstream task performance significantly (promoter VEP from 30%->40%) and very drastically improves distal task performance (ncRNA exon variants from 19%->65% and enhancer variants from 14%->33%) while mostly keeping performance on other tasks fixed
  - Our best recipe so far trains on a uniformly-weighted, 3-region mixture of sequence data proximal to genes (~104B tokens) followed by continued pretraining on a uniformly-weighted, 5-region mixture expanded to include distal sequences (~62B tokens)
    - This outperforms de novo training on the 5-region mixture
  - Conclusion: improving zero-shot performance mid-flight is possible by adding **new**, uniformly-weighted mixture components
    

## Conclusion

- Our net result is a PoC for a 1B model on par with Evo 2 40B after training on just 1.8% as many tokens (166B vs 9.3T) and ~0.05% as many FLOPs (1.1e21 vs 2.25e24)
  - Show Figure 10
- This model resulted from a messy, ad-hoc process aided in unanticipated ways by hyperparameter transfer, scaling and mixture tools within Marin
  - Many less successful attempts are not mentioned here but documented in https://github.com/Open-Athena/marin-dna
- Ongoing work will hopefully yield a more consistent, effective training strategy