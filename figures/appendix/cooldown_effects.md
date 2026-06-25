# Cooldown effects (m1 & m3 continuation chains)

A natural counterfactual from the two zoonomia pre-cooldown chains (`m1→m1.1→m1.2→m1.3`, `m3→m3.1→m3.2→m3.3`). At each fork a child resumes from the parent **before** the parent's learning-rate cooldown and keeps training at peak LR, while the parent finishes its own cooldown on a path the child never took. This lets us compare, at matched cumulative-token levels:

- **pre-cooldown** — the parent's eval at the fork (shared warm-start checkpoint, peak LR).
- **post-cooldown** — the parent's final eval after it cooled down.
- **continued (peak LR)** — the child's eval at the *same* cumulative tokens as the parent's cooled end, reached by staying at peak LR.

**Deltas** (relative to pre-cooldown): `Δ cooldown = post − pre` (effect of cooling down) and `Δ continued = continued − pre` (effect of spending the same extra tokens at peak LR instead). For `eval/loss` lower is better, so an improvement is **negative**; for VEP AUPRC higher is better, so an improvement is **positive**.

**speedup** `= Δ cooldown / Δ continued`: how many times larger the gain from cooling down is than the gain from spending the same extra tokens at peak LR. A value of e.g. 3× means cooldown achieved 3× the metric change that continued peak-LR training did over the same token budget. (Both deltas share a sign per metric, so the ratio is positive.)

> **Note on the terminal forks** (`m1.2→m1.3`, `m3.2→m3.3`): the child is the terminal leaf, which begins its own cooldown before reaching the parent's final token level, so its *continued (peak LR)* point is ~29% into the leaf's cooldown rather than pure peak LR. Those rows are flagged and excluded from the clean-fork averages below. The pre→post cooldown delta is unaffected.

Full per-metric data (all 8 VEP subsets) is in `cooldown_effects.csv`.

## Validation loss (`eval/loss`)

| fork | tokens (B) | pre-cooldown | post-cooldown | continued (peak LR) | Δ cooldown | Δ continued | speedup | note |
|---|---|---|---|---|---|---|---|---|
| m1->m1.1 | 50→62 | 1.169 | 1.135 | 1.158 | -0.034 | -0.010 | 3.2× |  |
| m1.1->m1.2 | 87→112 | 1.144 | 1.094 | 1.132 | -0.050 | -0.012 | 4.3× |  |
| m1.2->m1.3 | 112→149 | 1.132 | 1.072 | 1.105 | -0.060 | -0.027 | 2.3× | continued pt 29% into leaf cooldown |
| m3->m3.1 | 50→62 | 1.166 | 1.131 | 1.158 | -0.035 | -0.009 | 4.0× |  |
| m3.1->m3.2 | 87→112 | 1.140 | 1.090 | 1.130 | -0.050 | -0.010 | 5.0× |  |
| m3.2->m3.3 | 112→149 | 1.130 | 1.069 | 1.103 | -0.061 | -0.027 | 2.3× | continued pt 28% into leaf cooldown |
| **m1.x mean** | — | — | — | — | **-0.042** | **-0.011** | **3.8×** | mean of 2 clean forks |
| **m3.x mean** | — | — | — | — | **-0.043** | **-0.009** | **4.5×** | mean of 2 clean forks |

Mean over the 4 clean forks: Δ cooldown = -0.042, Δ continued = -0.010, speedup = 4.1×.

## VEP macro average (mean of 8 subsets)

| fork | tokens (B) | pre-cooldown | post-cooldown | continued (peak LR) | Δ cooldown | Δ continued | speedup | note |
|---|---|---|---|---|---|---|---|---|
| m1->m1.1 | 50→62 | 0.3489 | 0.3833 | 0.3672 | +0.0344 | +0.0182 | 1.9× |  |
| m1.1->m1.2 | 87→112 | 0.3759 | 0.4227 | 0.3922 | +0.0468 | +0.0163 | 2.9× |  |
| m1.2->m1.3 | 112→149 | 0.3922 | 0.4368 | 0.4189 | +0.0446 | +0.0267 | 1.7× | continued pt 29% into leaf cooldown |
| m3->m3.1 | 50→62 | 0.3690 | 0.3972 | 0.3756 | +0.0282 | +0.0066 | 4.3× |  |
| m3.1->m3.2 | 87→112 | 0.3921 | 0.4291 | 0.4092 | +0.0370 | +0.0171 | 2.2× |  |
| m3.2->m3.3 | 112→149 | 0.4092 | 0.4280 | 0.4292 | +0.0188 | +0.0200 | 0.9× | continued pt 28% into leaf cooldown |
| **m1.x mean** | — | — | — | — | **+0.0406** | **+0.0173** | **2.4×** | mean of 2 clean forks |
| **m3.x mean** | — | — | — | — | **+0.0326** | **+0.0119** | **2.7×** | mean of 2 clean forks |

Mean over the 4 clean forks: Δ cooldown = +0.0366, Δ continued = +0.0146, speedup = 2.5×.
