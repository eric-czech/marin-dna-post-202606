## Intro

- Scaling laws ideally require training at optimal configurations for all scales 
- Transfer is one way to accomplish this; Hyperball and Complete(d) make this possible
- WIP

## TODO

- Frame as post on technical nuances of running scaling law experiments
  - Experimentation is most of the work so how do you make that experimentation robust to changing capacity and experiment designs?
    - Batch sizing for the sake of experiment throughput is a big advantage
    - It is otherwise necessary to constantly be retuning
  - Discuss how transfer helps
  - What if a batch size exceeds HBM later in training?
  - What if you have to switch hardware with different HBM capacity?
- Find and discuss references on confounding in scaling laws from lack of tuning
- Add token counts to transfer figures to make scale clear
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

### Details

- In training, nucleotides in repeats are downweighted by a factor of 100 from 1 to .01
- In evaluation, nucleotides in annotated non-functional regions are downweighted by the same factor (100)