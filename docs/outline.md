## Intro

- Scaling laws ideally require training at optimal configurations for all scales 
- Transfer is one way to accomplish this; Hyperball and Complete(d) make this possible
- WIP

## TODO

- Compare predicted hypers at 1e23 scale to text models at that scale
- Create a table containing best hypers by FLOP and token count as a guideline for others 
    - Start with this to make it clear that transfer is a function of tokens
- Sweep stats: FLOPS and wall clock time
    - Use figure 4 of https://arxiv.org/pdf/2305.16264 w/ 4.2B param 85B token training (very similar to scale here) as reference point on how large these experiments are

## Stats

### Training data

- Spans 3 genomic regions: cds, upstream, downstream
- Context length is 255 bp (+BOS token for 256 total)
- Training: [CDS](https://huggingface.co/datasets/bolinas-dna/genomes-v5-genome_set-animals-intervals-v5_255_128) (242,334,716) | [Upstream](https://huggingface.co/datasets/bolinas-dna/genomes-v5-genome_set-animals-intervals-v1_255_128) (68,286,166) | [Downstream](https://huggingface.co/datasets/bolinas-dna/genomes-v5-genome_set-animals-intervals-v15_255_128) (20,501,856) = 331,122,738 total (~84.8B tokens) ([counts](https://gist.github.com/eric-czech/656b63dc78ac7792f5c5d824e0b5f103))
- Validation (16,384 each): [CDS](https://huggingface.co/datasets/bolinas-dna/genomes-v5-validation-intervals-v5_255_255) | [Upstream](https://huggingface.co/datasets/bolinas-dna/genomes-v5-validation-intervals-v1_255_255) | [Downstream](https://huggingface.co/datasets/bolinas-dna/genomes-v5-validation-intervals-v15_255_255)
- All have 366,411 unique RefSeq accessions spanning 500 distinct species
  - Mostly birds, with a long tail of fish, reptiles, mammals, arthropods, etc.
  - All accessions mapped cleanly in NCBI accession2taxid file with ~6K newest accessions filled in via Entrez esummary

### Eval (VEP) sample count by variant type

┌────────────────────────────────────┬────────┬─────────────────────┬────────┐   
│               subset               │   n    │ n_pos (target=True) │ n_neg  │
├────────────────────────────────────┼────────┼─────────────────────┼────────┤
│ (all)                              │ 24,530 │               2,453 │ 22,077 │
├────────────────────────────────────┼────────┼─────────────────────┼────────┤
│ missense_variant                   │ 14,800 │               1,480 │ 13,320 │
├────────────────────────────────────┼────────┼─────────────────────┼────────┤
│ splicing                           │  2,670 │                 267 │  2,403 │
├────────────────────────────────────┼────────┼─────────────────────┼────────┤
│ 5_prime_UTR_variant                │  2,100 │                 210 │  1,890 │
├────────────────────────────────────┼────────┼─────────────────────┼────────┤
│ tss_proximal                       │  1,800 │                 180 │  1,620 │
├────────────────────────────────────┼────────┼─────────────────────┼────────┤
│ non_coding_transcript_exon_variant │  1,150 │                 115 │  1,035 │
├────────────────────────────────────┼────────┼─────────────────────┼────────┤
│ distal                             │    780 │                  78 │    702 │
├────────────────────────────────────┼────────┼─────────────────────┼────────┤
│ 3_prime_UTR_variant                │    770 │                  77 │    693 │
├────────────────────────────────────┼────────┼─────────────────────┼────────┤
│ synonymous_variant                 │    460 │                  46 │    414 │
└────────────────────────────────────┴────────┴─────────────────────┴────────┘


## Figures

### Transfer Validation

- Figure 1: Learning Rate (η) Transfer
  - LR vs eval loss for each run in sweep
  - Group and color by model param count (line+scatter plot)
  - Assign shape to positive and negative controls (square) and others (circle)
- Figure 2: Beta2 (β2) / Epsilon (ε) Transfer
  - Same as LR plot, but 1x2 subplots for β2 and ε

### Parameter Scaling

- Figure 3: Train/Eval Loss Curves
  - Step vs loss for train and eval as 1x2 subplots
  - Group and color by model param count (line plot only)
- Figure 4: Params vs. VEP AUPRC
  - Include missense, tss_proximal, 5_prime_UTR_variant, 3_prime_UTR_variant, splicing, synonymous metrics
  - Use 1x3 subplots with metrics in task groups:
    - Upstream: tss_proximal, 5_prime_UTR_variant
    - CDS: missense, synonymous
    - Other: 3_prime_UTR_variant, splicing
  - Use "promoter" as display name for "tss_proximal"
  - Use unique legend per facet in upper left containing only relevant metrics
  - Group and color by variant type (line+scatter plot)
- Figure 5: Loss vs. VEP AUPRC
  - Include same variant types as figure 4
  - 2x3 subplots w/ order:
    - missense, tss_proximal, 5_prime_UTR_variant
    - 3_prime_UTR_variant, splicing, synonymous
  - Plot loss on x-axis and AUPRC on y-axis (scatter plot only)
  - Size dots by model param count

### Details

- In training, nucleotides in repeats are downweighted by a factor of 100 from 1 to .01
- In evaluation, nucleotides in annotated non-functional regions are downweighted by the same factor (100)