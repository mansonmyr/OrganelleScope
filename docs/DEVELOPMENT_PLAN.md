# Development plan and accepted scope

Working name: OrganelleScope. Academic research use. Repository visibility changed from private to public at the user's express request during implementation. No deletion of the original repositories is part of implementation.

## Intended release

- Desktop Windows 11 and Apple Silicon macOS, with a separate marketing/download website.
- Standard imaging target: native 16-bit, 2048×2048, up to four channels, typical Z extent 6–9 µm. Extent is not a slice-count limit. Read actual XY and Z calibration from metadata; never impose a nominal scale or exaggerate Z for measurements.
- Development hardware: Apple M3, 24 GB unified memory. Native Windows x64 testing remains necessary; Parallels on Apple Silicon usually tests Windows ARM/emulation.
- Static images and Z-stacks. Time-lapse tracking excluded.
- Human cells initially, including RPE/U2OS. Centrosomes, mitochondria, nuclei, microtubules, Golgi and user-defined compartments.
- Both measured control/knockdown comparisons and clearly distinguished hypothetical scenarios.
- Conventional widefield/confocal data are the main input. Computational restoration/reconstruction must have measurement-specific validation; sharper appearance is not proof of molecular resolution.
- Only metadata/specifications are currently available for calibration. Some super-resolution reference samples exist, but are separate samples, not registered pairs of the same cells. Unmeasured systematic errors remain explicit.

## Milestones

1. **Import and viewing foundation:** provenance, metadata conflicts, axes, native intensities, XY profiles, calibrated volume preview, source reconciliation, automated checks.
2. **Measurement engine:** explicit Pearson/Spearman/Manders definitions and threshold outcomes; 2D/3D ROIs; spatially appropriate nulls; source/processed comparison. No mock phenotype classifier or uncalibrated probability of binding.
3. **Preprocessing:** background estimators, optional Gaussian smoothing, residuals and full processing records. Noise2Void and deconvolution are excluded at the user’s request. Do not port the profiler's mean-filter subtraction under a rolling-ball label.
4. **Organelle workflows:** inspectable/editable segmentation with compartment-specific measurements, calibrated surfaces/distances, radial enrichment and multi-ROI projects. Multi-channel rendering, orthogonal linked slices and quality overlays.
5. **Inference:** appropriate image/noise likelihoods for MLE; Bayesian parameter uncertainty and visible priors; hierarchical experiment comparisons; bootstrap/Monte Carlo uncertainty propagation; model diagnostics and multiple-comparison control.
6. **Reconstruction validation:** representative conventional/SR references, held-out acquisitions, synthetic controls, failure-domain checks, artifact maps and downstream measurement bias. No arbitrary nanoscale distances from interpolation. Separate samples cannot establish pixel-level reconstruction ground truth.
7. **Molecular evidence and local agent:** UniProt identity mapping; STRING evidence types; academic KEGG; PubMed references. Approved external traffic is selected identifiers, species and literature queries. Images, measurements and conversations remain local. Rate limits, provenance, caching rights and offline state must be explicit.
8. **Release hardening:** reopenable projects, batch jobs, cancellation and recovery, memory budgets, offline models, signed distribution when credentials become available, GitHub release pipeline and marketing website.

The comprehensive first-public-release scope is retained. A module passing unit tests is not automatically scientifically validated. Unimplemented features must not appear as functioning controls.

## Agent/model decision

Initial evaluation candidate (0.1.7, now retired): Qwen3.5-4B, Q4_K_M via llama.cpp. See the active Ministral update below. One model in the full offline installer; do not bundle multiple competing models by default. Measure exact quantized-model tool use, numerical/citation fidelity, latency, memory and packaging size on target hardware. Model weights must have versioned manifests, hashes and notices before inclusion. The pinned community quantization and official llama.cpp runtime have now been downloaded and smoke-tested on M3/24 GB for source milestone 0.1.7. This is an experimental local agent, not a validated biological interpreter. Model/runtime assets are ignored development files, not committed weights or newly packaged installers. See LOCAL_ASSISTANT.md and ASSISTANT_EVALUATION.md.

Agent tools will inspect metadata, propose workflows, run deterministic analysis tools, inspect quality/sensitivity checks and retrieve evidence. Never alter settings to seek statistical significance, invent tool results, or interpret functional association as direct binding. Preserve raw data and make agent actions auditable/recoverable.

## Validation gates

- **Import:** known OME/ImageJ layouts, compressed/endian variants, anisotropic calibration, malformed/conflicting metadata, no implicit frame/series loss, UUIDs and source checksums.
- **Profiles:** analytical signals with known width/distance/AUC, variable sampling, anisotropic scale, edge-truncated and unresolved peaks, smoothing sensitivity.
- **Statistics:** matched reference implementations and documented conventions, degenerate inputs, spatially dependent nulls, controlled effect sizes and false-positive behavior.
- **Inference:** simulated known parameters, interval coverage under stated assumptions, identifiability/failure cases, sensitivity to priors/model mismatch, explicit unmeasured registration/labeling errors.
- **Restoration:** model reference tensors, identity/negative controls, residuals and measurement changes, held-out experimental validation. Do not use denoised values as unchanged independent photon counts.
- **Agent:** curated tasks with expected tool actions and evidence, rejection of unsupported probabilities/claims, prompt-injection handling for retrieved content, graceful offline behavior.
- **Distribution:** platform installation/startup tests, unsigned/signing status, offline launch, model integrity and low-memory behavior. CI artifacts are development artifacts until these gates pass.

## Implemented research foundations (0.1.5 source)

Deterministic XY background correction and Gaussian smoothing, matched-contrast previews and raw/processed measurements are available. The validation workspace adds reference checks, matched ROI sensitivity and a narrowly specified seeded toroidal-shift control. The 3D workspace adds linked source sections and full-resolution cuboid measurements, without claiming segmentation or true molecular resolution. Academic STRING/KEGG identifier and association/pathway queries are available with local caches and provenance. Curated biological validation of both measurements and the experimental LLM, independent Fiji benchmarks, experiment-level inference, compartment-aware null models, segmentation and larger-volume optimization remain outstanding. See RESEARCH_WORKSPACES.md for limits and assumptions.

## Implemented persistence and local assistant (0.1.7 source)

Manual versioned local projects now restore source associations and workspace reports, with source-integrity checks, atomic writes and revision conflicts. The bounded local assistant inspects saved metadata/results/evidence, runs numeric references and can repeat only an explicitly saved provider query. Recorded numerical quantities are presented separately from generated interpretation. Portable archives, autosave, multi-image experiments, broader agent actions and full offline packaging remain planned.

## Active model update (0.1.8 source)

The selected evaluation candidate is now the official Ministral 3 8B Instruct Q4_K_M (5.20 GB), replacing Qwen. Known retired development model assets are cleaned only after valid inference. Historical Qwen evaluation observations remain as provenance; they are not measurements of Ministral performance. Current model evidence and limitations are recorded in ASSISTANT_EVALUATION.md.

## Gemma evaluation update (0.1.9 source)

Gemma 4 12B Instruct official QAT Q4_0 is the selected replacement evaluation candidate. It uses the same owned local runtime and read-only tool boundaries. The evaluation also expands answer budgets and preserves critical threshold/background context, so observed differences must not be attributed solely to model weights. Current results belong in ASSISTANT_EVALUATION.md; no replacement installer is published by this source milestone.

## Active roadmap status — source 0.2.0

Implemented in this development run: actual CAREamics training/tiled inference and safe numeric model bundles; residual/background and quantitative processing checks; PSF-based 2D/3D Richardson–Lucy; preview PNG/camera/calibration snapshots; inspectable/editable threshold masks, calibrated surfaces/object measurements, conditional proximity and radial enrichment; cell/experiment aggregation, paired/independent permutation tests, hierarchical bootstrap and BH correction; optional Gaussian MLE and visible-prior Bayesian uncertainty with sensitivity checks; portable project archives (including active restoration artifacts), latest-workspace recovery autosave; restoration build variants, frozen-service smoke checks, dependency notices and installer checksums.

Completed independent implementation benchmark: 12 direct installed Coloc_2 cases for Pearson/Spearman/zero-threshold Manders. Held-out synthetic N2V and Gaussian-posterior simulations are retained with unfavorable results as well as successes. See RESTORATION_AND_INFERENCE.md. These tests do not substitute for biological validation.

Still open for the comprehensive public release: representative user control images and experiment labels, held-out acquisition/domain-shift validation, realistic bootstrap coverage and model mismatch checks, compartment-specific classifiers/null models beyond threshold masks, native Windows/large-image installation stress tests, visual interaction testing, distributable full-offline installer qualification, signing when credentials are available and marketing/download launch. The current local assistant remains a bounded read-only interpreter; autonomous modification of measurements and automatic LLM ROI drawing are not introduced.

A browser access-policy rejection prevented live UI inspection in this run. Automated component/build checks and numerical endpoint checks proceed, but visual QA is explicitly outstanding. The user has been asked for local validation-image paths while independent implementation continues.

## Biological validation deferred by user — 17 October 2026

The user could not locate the original control images and explicitly authorized continuing without biological validation. Continue numerical, synthetic and packaging checks; keep biological validation marked deferred and do not imply publication certification. No further control-image request is required to continue development.

## Scope change — source 0.2.1

The user withdrew Noise2Void denoising and deconvolution. Both are removed from execution, UI, dependencies and installer workflows; Gaussian smoothing/background subtraction explicitly remain. Small historical evaluation records and research artifacts are preserved, with old restored measurements excluded from new inference. Added requested XY/camera zoom and separate correction/ROI/association tabs, retaining a shared persistent preview. Earlier restoration status entries are historical, not the active roadmap.

## 0.2.2 viewer and documentation milestone

Independent per-channel LUTs are implemented for the single-image XY/volume/linked-section/preparation views and snapshot provenance. Measurement intensities remain unchanged. README is a concise entry point and MANUAL.md is the detailed current guide. Keep Gemma; no candidate download/model swap. Future viewer features remain subject to user priorities and independent implementation/verification. No separate viewer-inspired roadmap is published.

## 0.2.3 Workspace layout and sample QA

Project save/open/archive/recovery controls move into the Workspace sidebar. UI chrome uses #6DB1BF, #FFEAEC, #FDF0D5 and #83BCFF with dark readable text; scientific channel LUTs stay independent. The separate viewer-inspired roadmap and its current-document links are removed at the user's request. General software comparisons/citations remain factual references; no third-party implementation or dependency was introduced. User-provided local TIFFs support technical tests; biological marker mappings and independent replicate identities must be confirmed before control interpretation.


## 0.2.4 channel identity, interpretation and unenhanced previews

Editable channel identities, exact selected-plane signal checks, marker-consistent batch inference, native-range main previews and report-aware assistant context are implemented. The manual expands method-specific primary literature citations. Independent Coloc 2 checks now include explicit manual-threshold boundary conventions. See INTERPRETATION_AND_QC_0.2.4.md for observed results and limitations. Biological validation, realistic design-specific coverage, native Windows installation and signed release qualification remain separate gates; existing segmentation, batch Excel and experiment workflows are refined rather than presented as newly implemented features.
