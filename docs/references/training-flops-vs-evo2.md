<!-- Source: https://gist.github.com/eric-czech/58b8beb9da8e2ef81c54adf50ee83927 -->

Thread: https://chatgpt.com/share/6a3943e2-6b88-83ea-a737-e13eae9dacc8
Anchor: **Evo 2 40B = 2.25e24 FLOPs**

## Provenance-first table

| Family | Model | FLOPs to use | Ratio vs. Evo 2 | Under / over | Provenance |
|---|---:|---:|---:|---|---|
| **Gemma** | **Gemma 2 27B** | **2.1e24** | **0.93x** | Under | **Secondary table**, not directly pulled from Epoch in this pass. AI2's OLMo 2 model card lists `Gemma-2-27B` at `2.1e24` training FLOPs. [Source](https://huggingface.co/allenai/OLMo-2-0325-32B) |
| **Gemma** | **Gemma 3 27B** | **2.3e24** | **1.02x** | Essentially equal / over | **Epoch-derived via NeoSignal**, not developer-published FLOPs. NeoSignal shows `Training Compute 2.3e24 FLOP` and labels the data source as Epoch AI. [Source](https://neosignal.io/component/gemma-3-27b) |
| **Qwen** | **Qwen2.5-14B** | **1.6e24** | **0.71x** | Under | **Epoch CSV search-index snippet + secondary table.** The Epoch CSV search snippet shows Qwen2.5-14B with `1.6e24 FLOP`; AI2's table also lists `Qwen-2.5-14B` at `1.6e24`. [Epoch CSV](https://epoch.ai/data/large_scale_ai_models.csv), [AI2 table](https://huggingface.co/allenai/OLMo-2-0325-32B) |
| **Qwen** | **Qwen2.5-32B** | **3.5e24** | **1.56x** | Over | **Secondary table**, not directly pulled from Epoch in this pass. AI2 lists `Qwen-2.5-32B` at `3.5e24` training FLOPs. [Source](https://huggingface.co/allenai/OLMo-2-0325-32B) |
| **DBRX** | **DBRX** | **2.6e24** | **1.16x** | Over, close | **Epoch CSV search-index snippet.** The Epoch large-scale CSV snippet shows DBRX with `2.6e24` training FLOPs. [Source](https://epoch.ai/data/large_scale_ai_models.csv) |
| **OLMo** | **OLMo 2 32B** | **1.3e24** | **0.58x** | Under | **Primary / model-card table.** AI2 lists `OLMo-2-0325-32B` at `1.3e24` training FLOPs. [Source](https://huggingface.co/allenai/OLMo-2-0325-32B) |
| **OLMo** | **Olmo 3 32B** | **8.1e23** | **0.36x** | Under | **Primary / model-card table.** AI2's Olmo 3 model card lists `Olmo 3-32B` at `8.1 · 10^23` training FLOPs. [Source](https://huggingface.co/allenai/Olmo-3-1125-32B/blob/d395924db75bdca9a0eae1ac092a5af103df92ea/README.md) — **Caveat:** the Olmo 3 card uses a lower FLOPs accounting than the OLMo 2 card; on that same Olmo 3 table `OLMo 2-32B` is listed at `7.8e23` (vs the `1.3e24` from the OLMo 2 card used in the row above). So this `8.1e23` is not directly comparable to the OLMo-2-card-sourced rows here. |
| **Llama** | **Llama 3.1 8B** | **7.2e23** | **0.32x** | Under | **Secondary table.** AI2 lists `Llama-3.1-8B` at `7.2e23` training FLOPs. [Source](https://huggingface.co/allenai/OLMo-2-0325-32B) |
| **DeepSeek** | **DeepSeek-V2** | **~1.02e24** | **0.45x** | Under | **Derived only in this pass.** Based on `21B` active params and `8.1T` tokens from the DeepSeek-V2 paper. I did not validate an Epoch row. [Source](https://arxiv.org/html/2405.04434v2) |
| **DeepSeek** | **DeepSeek-V3** | **~3.29e24** | **1.46x** | Over | **Derived only in this pass.** Based on `37B` active params and `14.8T` tokens from the DeepSeek-V3 paper. The paper gives GPU-hours, not pretraining FLOPs directly. [Source](https://arxiv.org/abs/2412.19437) |
| **Llama** | **Llama 3 / 3.1 70B** | **~6.3e24** | **2.8x** | Over | **Derived only in this pass.** Based on `70B` params and roughly `15T` tokens. I did not validate an Epoch row for this one. [Source](https://ai.meta.com/blog/meta-llama-3/) |

## Best under/over pairs

| Family | Under Evo 2 | Over / at Evo 2 | How solid? |
|---|---:|---:|---|
| **Gemma** | Gemma 2 27B — **2.1e24** | Gemma 3 27B — **2.3e24** | Good; Gemma 3 is Epoch-derived via NeoSignal, Gemma 2 is from AI2's table |
| **Qwen** | Qwen2.5-14B — **1.6e24** | Qwen2.5-32B — **3.5e24** | Good; Qwen 14B has Epoch CSV snippet + AI2 table, Qwen 32B has AI2 table |
| **DeepSeek** | DeepSeek-V2 — **~1.02e24** | DeepSeek-V3 — **~3.29e24** | Useful but still derived-only here |
| **Llama** | Llama 3.1 8B — **7.2e23** | Llama 3.1 70B — **~6.3e24** | 8B is table-backed; 70B is derived-only here |
| **OLMo** | OLMo 2 32B — **1.3e24** / Olmo 3 32B — **8.1e23** | — | Both fully under Evo 2; OLMo 2 from its own card (`1.3e24`), Olmo 3 from the Olmo 3 card (`8.1e23`, lower accounting — see caveat above) |
