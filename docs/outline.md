## Intro

- Scaling laws ideally require training at optimal configurations for all scales 
- Transfer is one way to accomplish this; Hyperball and Complete(d) make this possible
- WIP

## Stats

- Dataset 
  - Sequence length: 256
  - 3 genomic regions: cds, upstream, downstream
  - Spans 
  - Seq len, examples, species, tokens by region (cds, upstream, downstream) and total
- Sweeps
  - FLOPS and wall clock time

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


<details><summary>species</summary>

```
# CDS (bolinas-dna/genomes-v5-genome_set-animals-intervals-v5_255_128)
The dataset contains 366,411 unique RefSeq accessions (the id field is <accession>:start-end_strand). Mapped via NCBI's nucl_gb + nucl_wgs accession2taxid files (with the ~6K newest accessions filled in via Entrez esummary), then resolved each
 taxid to its species-rank ancestor in NCBI taxonomy. All 366,411 accessions resolved cleanly to a species, yielding 500 distinct species (mostly birds, with a long tail of fish, reptiles, mammals, arthropods, etc.).

Outputs in /Users/eczech/tmp/bolinas_species_count/:
- accessions.txt — 366,411 unique accessions
- acc_taxid_raw.tsv — accession → taxid
- species.tsv — 500 species sorted by accession count (top: Phaethon lepturus 11,320; tail: Liolophura japonica 1)
```

</details>

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