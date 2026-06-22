<!-- Source: https://gist.github.com/eric-czech/378ce357063636b2903cff6775a7a2e7 -->

# Human variant-prioritization models vs Evo2

## Scope

This list is restricted to models/methods that present **human variant prioritization / variant-effect prediction** results, especially **ClinVar**, **OMIM/TraitGym**, BRCA/DMS, HGMD, COSMIC, gnomAD, or GWAS fine-mapping-style evaluations.

The main split is by how the Evo2 comparison is made:

| Bucket | Meaning |
|---|---|
| Zero-shot | No ClinVar/OMIM/HGMD labels are used to train the final scorer. Scores may come from likelihood ratios, embedding distances, conservation/evolutionary scores, or other unsupervised objectives. |
| Supervised / fine-tuned | Human variant labels or functional labels are used to train a classifier, probe, readout, or disease-specific model. These comparisons are not apples-to-apples with zero-shot Evo2 scoring. |

## Direct zero-shot vs Evo2

| Model | Human VEP benchmark | Evo2 comparator | Notes |
|---|---|---:|---|
| [GPN-Star](https://github.com/songlab-cal/gpn) | ClinVar, OMIM/TraitGym-style variants, HGMD, COSMIC, GWAS fine-mapped variants, gnomAD, DMS, DepMap | Evo2-40B among comparators | Alignment / phylogeny-based human VEP model. One of the strongest examples of a smaller or structurally informed model being compared against very large Evo2-style baselines. |
| [GPN-Promoter](https://www.biorxiv.org/content/10.1101/2025.02.11.637758v1) | Promoter-like OMIM / TraitGym-style regulatory variants | Evo2-40B | Narrower than GPN-Star. Relevant mainly for promoter-region variant prioritization. |
| [Carbon-3B](https://huggingface.co/HuggingFaceBio/Carbon-3B) | BRCA2, TraitGym Mendelian, ClinVar coding, ClinVar noncoding | Evo2-7B | Direct zero-shot comparison. Carbon-3B beats Evo2-7B on BRCA2 and ClinVar noncoding in the HF table, but trails on ClinVar coding and TraitGym Mendelian. |
| [GENERATOR-v2-3B](https://huggingface.co/HuggingFaceBio/Carbon-3B) | BRCA2, TraitGym Mendelian, ClinVar coding, ClinVar noncoding | Evo2-7B | Included as a comparator in the Carbon-3B evaluation table. Beats Evo2-7B on ClinVar noncoding there, but not on the other listed human VEP tasks. |
| [AIDO.DNA2](https://genbio.ai/aido-dna2-multi-species-genomic-pretraining-model/) | ClinVar SNV and non-SNV pathogenicity | Evo2-1B | Direct zero-shot ClinVar comparison, but against similarly scaled Evo2-1B rather than Evo2-7B or Evo2-40B. Uses embedding-distance-style scoring rather than Evo-style likelihood ratio. |
| [TrinityDNA-LabFauna](https://arxiv.org/html/2507.21706v1) | ClinVar-SNV zero-shot | Evo2-1B, Evo2-7B, Evo2-40B | Direct zero-shot ClinVar comparison. Appears competitive with Evo2 variants, but does not cleanly dominate Evo2-40B across all reported metrics. Worth manual checking because the table/text are somewhat awkward. |
| [BioFM / BioToken](https://www.researchgate.net/publication/390401808_BioToken_and_BioFM_-_Biologically-Informed_Tokenization_Enables_Accurate_and_Efficient_Genomic_Foundation_Models) | ClinVar / OMIM-style pathogenicity tasks, expression-modulating variants, sQTLs | Evo2-7B | Has direct zero-shot pathogenicity comparisons, but Evo2-7B is stronger on several zero-shot pathogenicity tasks. BioFM’s stronger claim is compute-efficient representation learning / probing, not clean zero-shot dominance. |

## Zero-shot, no direct Evo2 comparison

| Model | Human VEP benchmark | Notes |
|---|---|---|
| [GPN-MSA](https://github.com/songlab-cal/gpn) | ClinVar, COSMIC, OMIM, gnomAD | Key precursor to GPN-Star. Highly relevant alignment-based zero-shot human VEP model, but the original work is not itself an Evo2 comparison paper. |
| [PhyloGPN](https://arxiv.org/abs/2503.03773) | ClinVar and OMIM-style disease variants | Zero-shot phylogenetic/evolutionary human VEP model. Comparisons are mainly to GPN-MSA, nucleotide transformers, HyenaDNA-style models, etc., rather than direct Evo2 comparisons. |
| [ArGamba / Bi-Gamba](https://openreview.net/forum?id=jK0Fwy38oQ) | ClinVar pathogenicity ranking | Uses evolutionary-rate prediction as an efficient pretraining target. Relevant to human VEP, but the key ClinVar comparison table does not appear to include Evo2. |

## Supervised / fine-tuned

| Model | Human VEP benchmark | Notes |
|---|---|---|
| [EnTao-GPMFast / EnTao-GPMPro](https://arxiv.org/abs/2507.21706) | ClinVar / HGMD-style germline pathogenicity prediction | Fine-tuned pathogenicity predictors built from TrinityDNA-LabFauna. Relevant to human variant prioritization, but not zero-shot Evo2 comparators. |
| [BioFM / BioToken linear-probe results](https://www.researchgate.net/publication/390401808_BioToken_and_BioFM_-_Biologically-Informed_Tokenization_Enables_Accurate_and_Efficient_Genomic_Foundation_Models) | Coding/noncoding pathogenicity, expression-modulating variants, sQTLs | The more favorable BioFM-vs-Evo2 claims are mostly representation/probing results, which are supervised evaluations. |
| [AlphaGenome](https://www.nature.com/articles/s41586-025-10014-0) | Expression, splicing, polyadenylation, enhancer-gene linking, accessibility, TF binding, ClinVar splicing, fine-mapped eQTL/sQTL, caQTL/dsQTL | Strong supervised sequence-to-function model for human variant prioritization. Not an unsupervised Evo2-style scorer. |
| [Borzoi](https://www.nature.com/articles/s41588-024-02053-6) | RNA-seq / expression variant-effect prediction, eQTL-style tasks | Supervised human regulatory / transcriptomic sequence-to-function model. Important baseline, but not a zero-shot Evo2 comparison. |
| [Enformer](https://www.nature.com/articles/s41592-021-01252-x) | eQTL variant-effect prediction and fine-mapped variant classification | Older but central supervised sequence-to-function baseline for human regulatory variant prioritization. |
| [ChromBPNet](https://www.biorxiv.org/content/10.1101/2024.12.25.630221v2) | Fine-mapped GWAS variants, accessibility / TF-binding regulatory variant interpretation | Strong task-specific supervised regulatory variant baseline. Not a zero-shot Evo2-style model. |

## Strict zero-shot ClinVar / OMIM vs Evo2 shortlist

These are the models I would keep if the criterion is specifically:

> Human ClinVar / OMIM / TraitGym-style zero-shot variant prioritization with an explicit Evo2 comparison.

- GPN-Star
- GPN-Promoter
- Carbon-3B
- GENERATOR-v2-3B
- AIDO.DNA2
- TrinityDNA-LabFauna
- BioFM / BioToken

## Cleanest “small or efficient model beats Evo2 on at least some zero-shot human VEP tasks”

- GPN-Star
- Carbon-3B
- AIDO.DNA2, but only vs Evo2-1B
- GPN-Promoter, but only in a promoter-restricted slice
- GENERATOR-v2-3B, but mainly for ClinVar noncoding in the Carbon table

## Notes

- Caduceus is intentionally excluded here. Its original paper does not compare to Evo2 on zero-shot ClinVar / OMIM-style evaluation.
- EnTao-GPMFast and EnTao-GPMPro should be separated from TrinityDNA-LabFauna. TrinityDNA-LabFauna is the base model with zero-shot ClinVar-SNV comparison; EnTao-GPMFast/Pro are supervised pathogenicity predictors.
- AlphaGenome, Borzoi, Enformer, and ChromBPNet are highly relevant to human variant prioritization, but they belong in the supervised sequence-to-function bucket rather than the zero-shot Evo2-comparison bucket.
