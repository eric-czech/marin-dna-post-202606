## Misc

- The large majority (~80%) of compute resources required to train a modern LLM result from experimentation, not final models [https://arxiv.org/abs/2605.01158]
- Scaling laws ideally require training at optimal configurations for all scales 
  - Results can be significantly different otherwise
    - Cite https://arxiv.org/pdf/2406.19146
  - On learning rate and batch size scaling
    - https://arxiv.org/pdf/2503.04715
      - "The optimal learning rate follows a power-law relationship with N
and D, while the optimal batch size is primarily influenced by D and remains
largely invariant to N"
- Potential technical nuances of running scaling law experiments
  - Batch sizing for the sake of experiment throughput
  - Batch size exceeds HBM later in training
  - Switch hardware with different HBM capacity?
- On expense of scaling law experiments:
  - https://arxiv.org/pdf/2604.22753
  - "Scaling laws are used to plan multi-million-dollar training runs, but fitting those laws can itself cost millions"
  - "At industrial scale, the pilot runs needed just to fit a scaling law can themselves consume a massive budget (Porian et al., 2025; Hagele et al., 2024)"

## TODO

- Primary
  - Refactor "That cooldown behavior matching what we expect from text models is also somewhat noteworthy"
    - Include results from cooldown analysis
  - Sweep stats: FLOPS and wall clock time
    - Use figure 4 of https://arxiv.org/abs/2305.16264 w/ 4.2B param 85B token training (very similar to scale here) as reference point on how large these experiments are
  - Get throughput numbers
  - Mention loss masking
- Secondary
  - Compare predicted hypers at 1e23 scale to text models at that scale
  - Create a table containing best hypers by FLOP and token count as a guideline for others 
    - Start with this to make it clear that transfer is a function of tokens

## Stats

### Training data

- Spans 3 genomic regions: cds, upstream, downstream
- Context length is 255 bp (+BOS token for 256 total)
- All regions have 366,411 unique RefSeq accessions spanning 500 distinct species
  - Mostly birds, with a long tail of fish, reptiles, mammals, arthropods, etc.
  - All accessions mapped cleanly in NCBI accession2taxid file with ~6K newest accessions filled in via Entrez esummary

| Genomic region | Training examples | Training tokens | Validation examples | Validation tokens | HF dataset links |
| -------------- | ----------------: | --------------: | ------------------: | ----------------: | ---------------- |
| CDS            |       242,334,716 |  62,037,687,296 |              16,384 |         4,194,304 | [Training](https://huggingface.co/datasets/bolinas-dna/genomes-v5-genome_set-animals-intervals-v5_255_128) / [Validation](https://huggingface.co/datasets/bolinas-dna/genomes-v5-validation-intervals-v5_255_255) |
| Upstream       |        68,286,166 |  17,481,258,496 |              16,384 |         4,194,304 | [Training](https://huggingface.co/datasets/bolinas-dna/genomes-v5-genome_set-animals-intervals-v1_255_128) / [Validation](https://huggingface.co/datasets/bolinas-dna/genomes-v5-validation-intervals-v1_255_255) |
| Downstream     |        20,501,856 |   5,248,475,136 |              16,384 |         4,194,304 | [Training](https://huggingface.co/datasets/bolinas-dna/genomes-v5-genome_set-animals-intervals-v15_255_128) / [Validation](https://huggingface.co/datasets/bolinas-dna/genomes-v5-validation-intervals-v15_255_255) |
| **Total**      |   **331,122,738** | **84,767,420,928** |          **49,152** |    **12,582,912** | [Counts](https://gist.github.com/eric-czech/656b63dc78ac7792f5c5d824e0b5f103) |

### Eval (VEP) sample count by variant type

| Subset                               |      n | n_pos (target=True) |  n_neg |
| ------------------------------------ | -----: | ------------------: | -----: |
| (all)                                | 24,530 |               2,453 | 22,077 |
| missense_variant                     | 14,800 |               1,480 | 13,320 |
| splicing                             |  2,670 |                 267 |  2,403 |
| 5_prime_UTR_variant                  |  2,100 |                 210 |  1,890 |
| tss_proximal                         |  1,800 |                 180 |  1,620 |
| non_coding_transcript_exon_variant   |  1,150 |                 115 |  1,035 |
| distal                               |    780 |                  78 |    702 |
| 3_prime_UTR_variant                  |    770 |                  77 |    693 |
| synonymous_variant                   |    460 |                  46 |    414 |

### Sweeps

- Reference: ~25M params, 2.5B tok, 16k batch, 4E+17 FLOPs
- Transfer: ~1.1B params, 10B tok, 4k batch, 6.8E+19 FLOPs
    - vs Reference: 44× params, 4× tokens, 0.25× batch, 170× FLOPs
- Scaling: ~4B params, 84B tok, 1536 batch, 2.1E+21 FLOPs
    - vs Reference: 160× params, 34× tokens, 0.094× batch, 5,200× FLOPs

### FLOPs

#### Parameter scaling sweep (one run per model size)

| model params | training FLOPs |
| ------------ | -------------: |
| 46M          |       2.45e+19 |
| 76M          |       4.00e+19 |
| 128M         |       6.77e+19 |
| 255M         |       1.33e+20 |
| 476M         |       2.48e+20 |
| 1B           |       5.80e+20 |
| 2B           |       1.17e+21 |
| 4B           |       2.07e+21 |

#### Transfer validation sweep (per-run cost × n at each model size)

| model params |  n | run FLOPs | total FLOPs |
| ------------ | -: | --------: | ----------: |
| 255M         | 25 |  1.57e+19 |    3.93e+20 |
| 476M         | 25 |  2.92e+19 |    7.30e+20 |
| 1B           | 26 |  6.84e+19 |    1.78e+21 |


### Best model (mixture sweep)

Best-performing model overall: `1.7.2·L` = W&B run
`dna-bolinas-mix-v0.9-p1B-i24-exp135-zoonomia-m5.1`
(uniform → uniform_to_uniform_1 → zoonomia 1/5 mix; warm-started from the
fully-cooled uniform_to_uniform_1 checkpoint).

Cumulative token lineage — own new-portion tokens per stage; pre-cooldown
branches contribute 80% of the parent's own tokens, final-checkpoint branches 100%:

| stage   | run                  |     own tokens | contributes                        |
| ------- | -------------------- | -------------: | ---------------------------------- |
| 1·L     | uniform              | 52,439,285,760 | ×0.8 (pre-cooldown) → 41,951,428,608 |
| 1.7·L   | uniform_to_uniform_1 | 62,033,756,160 | ×1.0 (final) → 62,033,756,160        |
| 1.7.2·L | exp135-zoonomia-m5.1 | 62,033,756,160 | own                                |
| **Total** |                    |                | **166,018,940,928**                |

- FLOPs/token: **6.836797e+09** (from 1·L: 3.58516774639396e20 FLOPs / 52,439,285,760 tokens)
- Cumulative tokens: **166,018,940,928**
- Cumulative training FLOPs: **1.135038e+21** (≈1.14e21)
- vs Evo2 40B (9.3T tok, 2.25e24 FLOPs; [C.1. Model training FLOPS comparison](https://www.nature.com/articles/s41586-026-10176-5)): Evo2 = **~56× our tokens, ~1,980× our FLOPs**; i.e. we used **~1/56 the tokens (~1.8%)** and **~1/1,980 the FLOPs (~0.05%)**

### Details

- In training, nucleotides in repeats are downweighted by a factor of 100 from 1 to .01
- In evaluation, nucleotides in annotated non-functional regions are downweighted by the same factor (100)