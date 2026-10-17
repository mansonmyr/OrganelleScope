# Source notices

Required Notice: Copyright 2026 Kai Hong Ooi All rights reserved.

Derived components from [Quick IF Line Profiler](https://github.com/mansonmyr/Quick-IF-Line-Profiler): profile helpers, types, SignalChart, TIFF chart export and selected tests. Changes include corrected fractional-index distance conversion and sampling-aware smoothing. Original PolyForm Noncommercial 1.0.0 terms are in `Quick-IF-Line-Profiler.LICENSE`.

[Probabilistic Colocalization Estimator](https://github.com/mansonmyr/Probabilistic_Colocalization_Estimator) is a predecessor and migration source; its original terms are retained in `Probabilistic_Colocalization_Estimator.LICENSE`.

The repository now contains the user-provided GNU GPLv3 LICENSE at its root. These notices do not relicense predecessor code or third-party dependencies. Dependency and model license inventories must be completed before distribution. No N2V or LLM weights are tracked in Git or added to an installer by this milestone.


## Local assistant development assets

The active model is Gemma 4 12B Instruct, official Google QAT Q4_0 GGUF, revision `29d097773436b69ff9feafd636ab4cf873786537`, under Apache-2.0 (`Gemma-4-LICENSE.txt`). Exact file size and SHA-256 are in `backend/organelle_scope/local_model.py`.

The previous Qwen community quantization and Ministral model are retired. Their small historical licence records and evaluations remain as provenance; their local weights and temporary test files are removed after successful replacement inference.

The official llama.cpp b11669 runtime is from ggml-org. Its source licence is retained in `llama.cpp-LICENSE.txt`. The development setup verifies the official platform archive before extraction and retains the archive's bundled notices. The runtime and model are downloaded into ignored local folders; **neither their binaries nor weights are committed or added to an installer by this milestone**. Review all bundled-runtime dependency notices before any future redistribution.

The assessed Liquid LFM2.5-8B-A1B Q4_K_M candidate (official LiquidAI revision `49c14831707011e64d70b2ebd8462ba08d608434`) uses LFM Open License v1.0, retained in `Liquid-LFM-LICENSE.txt`. It is not the selected application model and its evaluated weights are removed after comparison. Its pinned assessment manifest is in `backend/organelle_scope/model_candidates.py`; the full licence must be reviewed before any future redistribution.

## Image processing — 0.2.1

CAREamics, PyTorch, torchvision and Lightning are no longer part of the application runtime. Small historical benchmark records remain as evaluation provenance. Current processing uses SciPy background estimators/Gaussian smoothing and scikit-image threshold/surface primitives. PYTHON_DEPENDENCY_NOTICES.txt is regenerated from the current build environment. User research artifacts from retired methods are preserved and can be archived; their presence does not enable new restoration processing.
