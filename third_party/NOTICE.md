# Component notices

Required Notice: Copyright 2026 Kai Hong Ooi All rights reserved.

Derived components from [Quick IF Line Profiler](https://github.com/mansonmyr/Quick-IF-Line-Profiler) include profile helpers, types, SignalChart, TIFF chart export and selected tests. Changes include corrected fractional-index distance conversion and sampling-aware smoothing. Original terms remain in [Quick-IF-Line-Profiler.LICENSE](Quick-IF-Line-Profiler.LICENSE).

[Probabilistic Colocalization Estimator](https://github.com/mansonmyr/Probabilistic_Colocalization_Estimator) is a predecessor and migration source; its original terms remain in [Probabilistic_Colocalization_Estimator.LICENSE](Probabilistic_Colocalization_Estimator.LICENSE).

The root GNU GPLv3 licence does not itself relicense predecessor or third-party components. Retain all applicable notices. certifi includes Mozilla Public License terms, retained in [certifi-LICENSE.txt](certifi-LICENSE.txt).

## Build-specific runtime notices

Each native build generates Python and frontend dependency notices plus a version inventory from its frozen module graph/runtime requirements and installed frontend production dependencies. These files are bundled in the installer's `resources/notices` directory (`Contents/Resources/notices` on macOS) and included in build artifacts. Electron supplies its own licence and Chromium notices. See [build instructions](../docs/DEVELOPMENT.md#dependency-notices).

CAREamics, PyTorch, torchvision and Lightning are excluded from the current runtime. Retired Qwen, Ministral and Liquid models are not distributed; historical assessments and licence provenance remain in Git history and the [model decision record](../README_MODEL_DECISIONS.md).

## Optional local assistant

Gemma 4 12B Instruct, official Google QAT Q4_0 GGUF, revision `29d097773436b69ff9feafd636ab4cf873786537`, uses Apache-2.0 ([Gemma-4-LICENSE.txt](Gemma-4-LICENSE.txt)). The active manifest records its exact file size and SHA-256.

The separately obtained official llama.cpp b11669 runtime uses the MIT licence ([llama.cpp-LICENSE.txt](llama.cpp-LICENSE.txt)); its downloaded archive retains additional bundled dependency notices. Compact release installers contain neither the model weights nor this optional runtime. Model/database terms are separate from the application licence; no STRING or KEGG database dump is bundled.
