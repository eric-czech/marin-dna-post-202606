Title: Optimal 
Subtitle: 

## Intro

- The large majority (~80%) of compute resources required to train a modern LLM result from experimentation, not final models [https://arxiv.org/abs/2605.01158]
- This means that if you want to build a language model, then you are likely to spend most of your time trying to determine:
  1. The influence of a single design choice in isolation
  2. How to actually isolate that choice
  3. Whether or not that choice will scale
- This experimentation frequently needs to compare results across different parameter, token and/or batch scales
- Scaling Laws are one obvious example for this kind of experimentation, as discussed in https://9dca63b0.openathena-ai.pages.dev/blog/delphi
- Scaling laws ideally require training at optimal configurations for all scales 
  - Results can be significantly different otherwise
    - Cite https://arxiv.org/pdf/2406.19146
  - On learning rate and batch size scaling
    - https://arxiv.org/pdf/2503.04715
      - "The optimal learning rate follows a power-law relationship with N
and D, while the optimal batch size is primarily influenced by D and remains
largely invariant to N"
- Transfer is one way to accomplish this; Hyperball and Complete(d) make this possible
- WIP


## TODO

- Frame as post on technical nuances of running scaling law experiments
  - Experimentation is most of the work so how do you make that experimentation robust to changing capacity and experiment designs?
    - Batch sizing for the sake of experiment throughput is a big advantage
    - It is otherwise necessary to constantly be retuning
    - References:
      - https://arxiv.org/pdf/2604.22753
        - "Scaling laws are used to plan multi-million-dollar training runs, but fitting those laws can itself cost millions"
        - "At industrial scale, the pilot runs needed just to fit a scaling law can themselves
consume a massive budget (Porian et al., 2025; Hagele et al., 2024)"
  - Discuss how transfer helps
  - What if a batch size exceeds HBM later in training?
  - What if you have to switch hardware with different HBM capacity?
- Find and discuss references on confounding in scaling laws from lack of tuning
- Add token counts to transfer figures to make scale clear
    - See stats/sweeps below
- Compare predicted hypers at 1e23 scale to text models at that scale
- Create a table containing best hypers by FLOP and token count as a guideline for others 
    - Start with this to make it clear that transfer is a function of tokens
- Sweep stats: FLOPS and wall clock time
    - Use figure 4 of https://arxiv.org/pdf/2305.16264 w/ 4.2B param 85B token training (very similar to scale here) as reference point on how large these experiments are

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


### Details

- In training, nucleotides in repeats are downweighted by a factor of 100 from 1 to .01
- In evaluation, nucleotides in annotated non-functional regions are downweighted by the same factor (100)