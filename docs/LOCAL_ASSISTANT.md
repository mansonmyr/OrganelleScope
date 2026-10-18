# Local assistant setup and operation

The experimental local assistant interprets supplied measurements and evidence. It does not certify biological conclusions or change analysis settings. The [manual](../MANUAL.md#part-xi--local-assistant-and-model-decisions) describes its user-facing workflow.

## Save and reopen a project

Use **Project name → Save project**. **Save as new** creates an independent snapshot; **Open saved project** restores it. A project currently contains one imported image, or an evidence-only workspace. Save before changing imports or quitting. The interface identifies unsaved changes. Saving is optional for assistant use: the desktop UI sends a question-time snapshot of the current workspace, including unsaved settings. Save after an assistant response only if you want that conversation retained in a project.

Snapshots preserve source identity, axes/calibration, XY ROIs and the selected line, processing recipes and measurement source, thresholds, XY results, Z/workspace selection, 3D channel/opacity/cutoff/Z-stretch, orthogonal positions/cuboid settings and reports, validation inputs/reports, molecular selections/reports/diagram provenance and the last twenty assistant turns with tool records. Line profiles are recomputed from the restored source and selected line. A rotated camera position, in-progress polygon vertices, unapplied preparation edits, temporary dialogs and running jobs are not saved.

The imported TIFF already resides in the local image store; project JSON references it rather than duplicating a large stack. Source SHA-256 is checked when reopening. If another import-setting edit changed its calibration/axes, reopening creates an isolated import association with the saved metadata, preserving the other association. Atomic JSON replacement avoids partial writes, and revisions prevent silent overwriting by a second window. A project whose original source is missing or changed is rejected. Portable project archives and the separate workspace recovery copy are documented in the manual. Back up the image store **and** its sibling `project-data` folder together. Project metadata/reports are currently capped at 16 MiB. The selector lists the fifty most recently saved projects; older project files are retained on disk.

Development locations: `.dev-images/`, `project-data/`, `evidence-cache/` and `assistant/` in the repository directory. Packaged applications use their existing application-data location and sibling folders. None of these folders belongs in Git. Saved evidence reports remain in the project; diagram pixels are in the bounded evidence cache and can be re-fetched with their provenance. A project snapshot is not an archival copy of the entire KEGG database.

## Questions without a saved project

The Ask button requires a nonblank question and no other question already running in this panel. It is not gated on having an image, a saved project, database acknowledgement, online permission or the Ready indicator. If installed model/runtime files are available, asking starts the local model and waits up to two minutes for readiness. Missing or modified model files and runtime failures return an actionable error; no model is downloaded implicitly, and the question remains in the textbox.

General methodology questions are allowed with no image. With an image selected, the UI supplies its identifier and metadata plus current settings/reports, not pixel data. This transient context is capped at 16 MiB and never creates a project. Reports whose source/calibration provenance differs from the selected import are excluded with a note. Unapplied preparation drafts are not measurements. Saving still preserves conversations and workspace state optionally. The older saved-project API remains available for reproducible evaluation scripts.

Online refresh is a separate optional permission to repeat the selected evidence query. With permission off, inference remains available using local context, model knowledge and cached evidence. Academic-use/offline database rules apply to the database request, not to general model use. General questions without image/evidence context do not require a fabricated project citation; unsupported source IDs, URLs and generated quantitative measurement claims remain checked. The bounded read-only tool loop and model integrity checks remain in place.

The assistant now receives a compact application-method reference clarifying Pearson's affine invariance, constant-channel undefined cases, directional Manders fractions, background methods and the distinction between likelihoods, posteriors, colocalization and binding. This reduces known prompt ambiguity but does not validate answers. Historical candidate comparisons used their recorded earlier prompts; their results must not be relabelled as evaluations of this updated prompt.

## Exact local model

- Upstream: [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it), Apache-2.0.
- Quantization: **official Google QAT GGUF**, [google/gemma-4-12B-it-qat-q4_0-gguf](https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf), revision `29d097773436b69ff9feafd636ab4cf873786537`.
- File: `gemma-4-12b-it-qat-q4_0.gguf`, **6,975,879,296 bytes** (6.98 GB / 6.50 GiB).
- SHA-256: `93567e57a8fe10b23569b9d9ec38cd005deedf71e29477c421a4b83f418a538b`.
- Runtime: official [llama.cpp b11669](https://github.com/ggml-org/llama.cpp/releases/tag/b11669); archive size/hash pinned in `scripts/setup-local-assistant.py`.
- Text-only use; no vision projector or raw image input. Context: 8,192 tokens; one request at a time; at most four model-selected tool calls plus the supplied workspace/project context. Google's recommended sampling settings are used: temperature 1.0, top-p 0.95 and top-k 64. Thinking is disabled for the bounded interactive tool loop; no internal reasoning is displayed or saved. The answer budget is 1,600 tokens (1,200 for a validation rewrite), with a prompt limit of three hundred words. Quantitative values remain engine-derived, independent of the language model.

These weights are **not** the full-precision model evaluated in upstream benchmarks. A successful local test does not transfer all upstream benchmark claims to this quantization or to microscopy interpretation.

## Installed application setup

The installed desktop app bundles the pinned local runtime and automatically starts the 6.98 GB weight download on first launch. A banner shows progress, pause and resume. The download uses a fixed HTTPS source/revision, validates resumed ranges, checks available disk space and requires exact size/SHA-256 before atomic installation. Partial files remain resumable; a corrupt complete download is discarded. Cancellation does not remove images or analysis data. Completed setup enables offline local inference without Python, Ollama, an API key or a separate model installation. Source checkouts do not automatically download weights.

## Explicit development setup

With the documented backend environment installed:

```sh
backend/.venv/bin/python scripts/setup-local-assistant.py --download
```

On native Windows x64 use `backend\.venv\Scripts\python.exe`. The script selects the pinned Apple Silicon Metal runtime or Windows x64 CPU runtime, verifies downloaded bytes before installation, and stores them under ignored `.local-runtime/` and `.local-models/`. Running without `--download` only prints the manifest. Source setup is explicit. Installed releases automatically set up the weights on first launch, independently of image import; the runtime is already bundled.

Apple Silicon has been smoke-tested on the development M3/24 GB system. Native Windows CPU runtime execution and installation are **not yet qualified**; Parallels/Windows ARM is not a native Windows x64 qualification. Custom bundled locations can be supplied using `ORGANELLESCOPE_LLAMA_SERVER` and `ORGANELLESCOPE_MODEL`; the pinned model checksum still applies. Compact release installers bundle the runtime and download the weights through integrated first-launch setup. Optional full-offline packaging has not been qualified for distribution.

Start the development app and open **Local assistant**. Enter a question and choose **Ask local assistant**; an installed model starts automatically. **Start local model** is also available to load it in advance. No project save or online lookup is required. **Unload model** releases the owned process. The app also stops its owned model on normal backend shutdown. No subscription, cloud inference service, API key or Ollama installation is needed. The loopback server uses a random port/session secret; no arbitrary remote inference endpoint is accepted.

## What the assistant can do

- Answer general methodology questions without an image or saved project.
- Read current image metadata/calibration and applied settings, including unsaved workspace changes.
- Read matching current ROI/3D/validation reports.
- Read selected STRING/KEGG evidence and its actual provenance.
- Run deterministic numerical reference checks.
- Repeat **the exact selected evidence query**. Default: cache only. Online refresh requires the explicit question-level checkbox; the current academic-use acknowledgement and offline-only preference still apply. No free-form model-selected URL or new protein query is executed.

The tool record is visible with each response. Only selected identifiers and evidence query parameters can leave the machine for the existing provider integrations; images, measurements and conversation text stay local. KEGG maps remain available in **Molecular evidence → View diagram**. Opening diagrams through the assistant, PubMed retrieval, applying proposed recipes and running new image measurements through agent tools are not implemented here.

## Interpretation safeguards and limits

Calculations remain in the deterministic engine. The assistant's interpretation is a draft. Recorded calibration/ROI quantities are displayed separately from generated prose, using supplied engine values and matching source/metadata provenance. The assistant is instructed to describe them qualitatively. The response checker normalizes full-width digits and hyphen/dash variants, then rejects numeric value patterns, fabricated source identifiers and model-provided URLs; one schema-constrained rewrite is attempted with citations restricted to supplied source IDs, then an invalid response is withheld. Protein identifiers such as TP53 and TUBG1, source identifiers and exact recorded channel/ROI labels can contain digits. A recorded label such as Channel 3 is accepted verbatim; this does not permit generating a measurement with the same digits elsewhere. Exact human KEGG gene IDs read from evidence tools are permitted verbatim despite containing digits; altered or unknown human KEGG gene IDs are rejected. This is not a general gene-symbol validator or citation-entailment check. These checks are practical constraints, **not a semantic proof that every sentence is correct**. Spelled-out values or qualitative overclaims still require evaluation and human review.

The allowlist has no shell, arbitrary filesystem, arbitrary URL, image modification or setting-write tool. Tool arguments/roles/budgets are validated. Retrieved data is treated as untrusted context. Provider association scores are not binding probabilities; pathway membership is not measured activation; hypothetical perturbations are hypotheses, not causal predictions. Missing measurements are not zero effects. No autonomous search for significance is allowed.

An automatic bounded measurement summary supplies selected ROI settings and metrics before generation; the full report remains available through read_measurements. Compact interpretation context retains selected threshold/background settings even when a large raw report is truncated. Missing documentation must be described as undocumented, rather than proof a control was never performed. General methodological advice must be distinguished from claims supported by database records. These are prompt/data improvements, not enforced scientific guarantees.

Engineering tests cover revisions/source integrity, restoration isolation, persisted workspace reports, tool permissions, offline query boundaries, model context format and invalid-reference/quantitative-answer rejection. Real model tests and their limitations are recorded in the [preserved assessment](../README_MODEL_DECISIONS.md#preserved-assessment-assistant-evaluation). Curated biological interpretation, citation-entailment assessment, prompt-injection robustness and native platform qualification remain release gates.


## Disk-space policy

One active model is retained. After the first valid assistant response, known superseded Qwen/Ministral weights, their incomplete download and obsolete development scratch files are removed from the managed local folders. Downloaded runtime archives are removed too; setup retains an integrity receipt for the installed runtime so a repeat setup can verify it without downloading the archive again. Model hashes/revisions and small evaluation summaries remain in source control. The current runtime, model and licence records are retained.

The cleanup allowlist does not remove images, saved projects, conversations, ROI/measurement reports, scientific evidence, user exports, custom models or unrelated files. Symlinked managed directories are skipped. Source updates also remove obsolete generated builds and superseded installers after identifying them, while keeping the most recent usable installer until it is replaced.

## Candidate assessment

Gemma remains the selected model after [the Liquid comparison](../README_MODEL_DECISIONS.md#preserved-assessment-liquid-comparison). The pinned Liquid profile is retained only for reproducible assessment; its temporary weights are removed after review. `scripts/setup-local-assistant.py --candidate liquid --download` explicitly downloads it without changing the app model. Run `scripts/evaluate-local-assistant.py --model gemma` or `--model liquid`, with a local `--output` path, sequentially against the named development fixtures. Both use the same application safeguards; different vendor sampling/thinking profiles are documented. This is not a model-selection setting exposed to application users or an installer change.

## Current-context smoke checks — 17 October 2026

A general Pearson question completed with no image, no saved project and online refresh unchecked. A targeted retest with the application-method reference correctly described Pearson's invariance to positive uniform rescaling under the stated conditions (29.31 seconds reported by the agent loop; not a controlled performance benchmark).

An image-specific question exposed two integration problems: exact recorded labels such as Channel 3 could trigger the quantitative-prose filter, and the old tool note incorrectly equated every null with “not measured.” The label check now accepts only exact supplied channel/ROI identifiers without allowing their digits as quantities elsewhere. The measurement summary now explicitly distinguishes an absent report from an undefined metric inside a completed report, includes recorded channel variation and zero-intensity flags, and explains that changing thresholds cannot repair a constant-channel Pearson correlation.

The repeated current-ROI question, still without saving or online refresh, correctly identified the zero-variation channel, undefined Pearson/Spearman and the distinction from biological absence (57.65 seconds reported by the loop). These targeted checks establish functioning context delivery and document observed answers; they do not certify general scientific reliability. The earlier ambiguous context can contribute to interpretation failures, so failures must not automatically be attributed solely to model weights.

## Current modality and selection clarification — 0.2.2

Text-only describes this application input path, not an inherent limit of upstream Gemma 4 12B. No image pixels are sent to the current assistant. The [model assessment](../README_MODEL_DECISIONS.md#preserved-assessment-model-selection) records Google's multimodal card, possible Llama Vision replacement, optional Qwen2-VL and GPT-OSS comparisons; none has replaced the active model.

## Claim review

Generated drafts now pass a separate, bounded automatic source audit. It checks record quotations, critical-topic coverage and claim scope, and exposes evidence links/quotes in the interface. The reviewer uses the same Gemma weights; it is not an independent reviewer and cannot guarantee semantic entailment or biological correctness. Unseen synthetic-question results retain withheld drafts and operational failures. See the manual and verification status.

## Memory and disk requirements

The weight file is 6.98 GB, not the total memory requirement. Leave at least about 7.5 GB of free disk space for setup, and additional space for research images. A computer with at least 16 GB RAM is recommended for the retained 12B profile; the development target is an M3 with 24 GB. Model context, native libraries, the viewer and TIFF stacks consume memory in addition to weights. Smaller-memory computers may be slow or unable to load this profile; image analysis remains independent of model setup. These are engineering recommendations, not universal hardware qualification.
