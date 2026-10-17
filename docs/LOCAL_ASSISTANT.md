# Local assistant and project persistence — source milestone 0.1.8

This milestone adds a working **experimental** local assistant and manually saved projects. It does not publish a new installer, certify biological conclusions, or enable autonomous analysis changes.

## Save and reopen a project

Use **Project name → Save project**. **Save as new** creates an independent snapshot; **Open saved project** restores it. A project currently contains one imported image, or an evidence-only workspace. Save before changing imports or quitting. The interface identifies unsaved changes; the assistant explicitly uses the last saved revision. Save again after an assistant response to retain that conversation.

Snapshots preserve source identity, axes/calibration, XY ROIs and the selected line, processing recipes and measurement source, thresholds, XY results, Z/workspace selection, 3D channel/opacity/cutoff/Z-stretch, orthogonal positions/cuboid settings and reports, validation inputs/reports, molecular selections/reports/diagram provenance and the last twenty assistant turns with tool records. Line profiles are recomputed from the restored source and selected line. A rotated camera position, in-progress polygon vertices, unapplied preparation edits, temporary dialogs and running jobs are not saved.

The imported TIFF already resides in the local image store; project JSON references it rather than duplicating a large stack. Source SHA-256 is checked when reopening. If another import-setting edit changed its calibration/axes, reopening creates an isolated import association with the saved metadata, preserving the other association. Atomic JSON replacement avoids partial writes, and revisions prevent silent overwriting by a second window. A project whose original source is missing or changed is rejected; source recovery and portable project archives are future work. Back up the image store **and** its sibling `project-data` folder together. Project metadata/reports are currently capped at 16 MiB. The selector lists the fifty most recently saved projects; older project files are retained on disk. Pagination is a future project-browser improvement.

Development locations: `.dev-images/`, `project-data/`, `evidence-cache/` and `assistant/` in the repository directory. Packaged applications use their existing application-data location and sibling folders. None of these folders belongs in Git. Saved evidence reports remain in the project; diagram pixels are in the bounded evidence cache and can be re-fetched with their provenance. A project snapshot is not an archival copy of the entire KEGG database.

## Exact local model

- Upstream: [mistralai/Ministral-3-8B-Instruct-2512](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512), Apache-2.0.
- Quantization: **official Mistral GGUF**, [mistralai/Ministral-3-8B-Instruct-2512-GGUF](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512-GGUF), revision `0102285ad796bd99af90f58de616092e5630e970`.
- File: `Ministral-3-8B-Instruct-2512-Q4_K_M.gguf`, **5,198,911,904 bytes** (5.20 GB / 4.84 GiB).
- SHA-256: `33e7a72cf5e6e2cfc2f2847075acc013d68bba023e35310cef86b5cf8fdca761`.
- Runtime: official [llama.cpp b11669](https://github.com/ggml-org/llama.cpp/releases/tag/b11669); archive size/hash pinned in `scripts/setup-local-assistant.py`.
- Text-only use; no vision projector or raw image input. Context: 8,192 tokens; one request at a time; at most four model-selected tool calls plus the supplied project context. Temperature is 0.05, following Mistral's recommendation below 0.1. Quantitative values remain engine-derived, independent of the language model.

These weights are **not** the full-precision model evaluated in upstream benchmarks. A successful local test does not transfer all upstream benchmark claims to this quantization or to microscopy interpretation.

## Explicit development setup

With the documented backend environment installed:

```sh
backend/.venv/bin/python scripts/setup-local-assistant.py --download
```

On native Windows x64 use `backend\.venv\Scripts\python.exe`. The script selects the pinned Apple Silicon Metal runtime or Windows x64 CPU runtime, verifies downloaded bytes before installation, and stores them under ignored `.local-runtime/` and `.local-models/`. Running without `--download` only prints the manifest. Downloading model/runtime assets is never an automatic side effect of importing an image or starting the application.

Apple Silicon has been smoke-tested on the development M3/24 GB system. Native Windows CPU runtime execution and installation are **not yet qualified**; Parallels/Windows ARM is not a native Windows x64 qualification. Custom bundled locations can be supplied using `ORGANELLESCOPE_LLAMA_SERVER` and `ORGANELLESCOPE_MODEL`; the pinned model checksum still applies. The desktop installer does not bundle these assets in this milestone. Full offline installer integration remains a release task, including complete dependency notices and platform signing.

Start the development app, save a project, open **Local assistant → Start local model**, and wait for **Ready**. **Unload model** releases the owned process. The app also stops its owned model on normal backend shutdown. No subscription, cloud inference service, API key or Ollama installation is needed. The loopback server uses a random port/session secret; no arbitrary remote inference endpoint is accepted.

## What the assistant can do

- Read saved image metadata/calibration and settings.
- Read saved ROI/3D/validation reports.
- Read saved STRING/KEGG evidence and its actual provenance.
- Run deterministic numerical reference checks.
- Repeat **the exact last saved evidence query**. Default: cache only. Online refresh requires the explicit question-level checkbox; the saved academic-use acknowledgement and offline-only preference still apply. No free-form model-selected URL or new protein query is executed.

The tool record is visible with each response. Only selected identifiers and evidence query parameters can leave the machine for the existing provider integrations; images, measurements and conversation text stay local. KEGG maps remain available in **Molecular evidence → View diagram**. Opening diagrams through the assistant, PubMed retrieval, applying proposed recipes and running new image measurements through agent tools are not implemented here.

## Interpretation safeguards and limits

Calculations remain in the deterministic engine. The assistant's interpretation is a draft. Recorded calibration/ROI quantities are displayed separately from generated prose, using saved engine values and matching source/metadata provenance. The assistant is instructed to describe them qualitatively. The response checker rejects numeric value patterns, fabricated source identifiers and model-provided URLs; one schema-constrained rewrite is attempted with citations restricted to supplied source IDs, then an invalid response is withheld. Protein identifiers such as TP53 and TUBG1 and source identifiers can contain digits. These checks are practical constraints, **not a semantic proof that every sentence is correct**. Spelled-out values or qualitative overclaims still require evaluation and human review.

The allowlist has no shell, arbitrary filesystem, arbitrary URL, image modification or setting-write tool. Tool arguments/roles/budgets are validated. Retrieved data is treated as untrusted context. Provider association scores are not binding probabilities; pathway membership is not measured activation; hypothetical perturbations are hypotheses, not causal predictions. Missing measurements are not zero effects. No autonomous search for significance is allowed.

Engineering tests cover revisions/source integrity, restoration isolation, persisted workspace reports, tool permissions, offline query boundaries, model context format and invalid-reference/quantitative-answer rejection. Real model tests and their limitations are recorded in `docs/ASSISTANT_EVALUATION.md`. Curated biological interpretation, citation-entailment assessment, prompt-injection robustness and native platform qualification remain release gates.


## Disk-space policy

One active model is retained. After the first valid assistant response, known superseded Qwen weights, their incomplete download and obsolete development scratch files are removed from the managed local folders. Downloaded runtime archives are removed too; setup retains an integrity receipt for the installed runtime so a repeat setup can verify it without downloading the archive again. Model hashes/revisions and small evaluation summaries remain in source control. The current runtime, model and licence records are retained.

The cleanup allowlist does not remove images, saved projects, conversations, ROI/measurement reports, scientific evidence, user exports, custom models or unrelated files. Symlinked managed directories are skipped. Source updates also remove obsolete generated builds and superseded installers after identifying them, while keeping the most recent usable installer until it is replaced.
