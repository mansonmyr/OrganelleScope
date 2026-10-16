# Source notices

Required Notice: Copyright 2026 Kai Hong Ooi All rights reserved.

Derived components from [Quick IF Line Profiler](https://github.com/mansonmyr/Quick-IF-Line-Profiler): profile helpers, types, SignalChart, TIFF chart export and selected tests. Changes include corrected fractional-index distance conversion and sampling-aware smoothing. Original PolyForm Noncommercial 1.0.0 terms are in `Quick-IF-Line-Profiler.LICENSE`.

[Probabilistic Colocalization Estimator](https://github.com/mansonmyr/Probabilistic_Colocalization_Estimator) is a predecessor and migration source; its original terms are retained in `Probabilistic_Colocalization_Estimator.LICENSE`.

The new application license is undecided. These notices do not relicense predecessor code or third-party dependencies. Dependency and model license inventories must be completed before distribution. No N2V or LLM weights are tracked in Git or added to an installer by this milestone.


## Local assistant development assets

Qwen3.5-4B is provided by Qwen under Apache-2.0; the model licence is retained in `Qwen3.5-4B-LICENSE.txt`. The pinned Q4_K_M file is a **community quantization**, from `lmstudio-community/Qwen3.5-4B-GGUF`, revision `f9f88ac3e234be915e23811a6d28ea287bdb927e`, not an official Qwen quantization. File size and SHA-256 are in `backend/organelle_scope/local_model.py`.

The official llama.cpp b11669 runtime is from ggml-org. Its source licence is retained in `llama.cpp-LICENSE.txt`. The development setup verifies the official platform archive before extraction and retains the archive's bundled notices. The runtime and model are downloaded into ignored local folders; **neither their binaries nor weights are committed or added to an installer by this milestone**. Review all bundled-runtime dependency notices before any future redistribution.
