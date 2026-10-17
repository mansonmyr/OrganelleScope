# Foundation verification — 16 October 2026

This records engineering checks for the first milestone. It is not a biological validation certificate.

- 27 backend tests pass in an isolated environment. Coverage includes OME/ImageJ scale extraction, generic print-DPI refusal, source identity, persistent-record refresh, axis confirmation, all C/Z planes, compressed/endian variants and bounded calibrated volume geometry.
- 18 frontend tests pass, including the analytical Gaussian FWHM regression across 0.5, 1 and 2 pixel sampling intervals.
- Frontend type checking and production build pass.
- All 15 supplied PCE TIFF examples open through the new importer in their source uint8/uint16 type. These examples were inspected locally and were not uploaded.
- Browser verification on a generated four-channel synthetic 31-plane OME stack confirms channel names, 0.100 × 0.100 × 0.250 µm spacing and an interactive single-channel 3D preview. This small-volume check does not establish performance on 2048×2048 stacks.
- Electron desktop startup and its session-authenticated image-service connection have been observed on the development Mac.
- The backend freezes successfully in an isolated environment (approximately 55 MB before adding scientific/AI modules). The frozen process starts and imports a synthetic OME stack without an external Python process.
- GitHub checks pass on Windows, macOS and Linux for the initial foundation.
- Both unsigned macOS ARM64 DMG and Windows x64 installer packaging jobs passed for development tag `v0.1.0-dev.1`: https://github.com/mansonmyr/OrganelleScope/actions/runs/38868850650

The installers are development artifacts, not the requested comprehensive release. They do not contain the local LLM, denoising/restoration models, full colocalization/inference engine, segmentation workflows or biological evidence integrations. Native installation tests of the generated artifacts and external-machine/GPU tests remain outstanding. A Parallels functional check does not substitute for native Windows x64 hardware testing.

Frontend dependency installation reported zero audit findings after updates. Desktop build tooling reported moderate-severity findings and requires further review before a public production release. Signing credentials are not available; no Developer ID signing/notarization or Windows publisher certificate is claimed.

The release scope and remaining scientific validation gates are tracked in DEVELOPMENT_PLAN.md. Neither a passing build nor an attractive reconstruction establishes accuracy of inferred nanoscale structure.

## ROI restoration verification

Six additional backend tests cover analytic Pearson/Spearman/overlap/Manders cases, undefined constant-channel cases, polygon boundaries and intersection rejection, circle masks, signed/collinear regression, automatic thresholds versus an independent brute-force pixel search, and authenticated API persistence on the correct native Z plane. Saved analyses are rejected after calibration settings change. Three interface tests cover circle completion, explicit polygon completion, Z-specific visibility and disabling drawing during calculation. Browser verification uses generated synthetic images only; biological validation against real experiments and independent software remains outstanding.

## Publication-readiness gate

The current development build is **not yet publication validated**. Exported analyses record this status. Numerical comparisons of Pearson and Spearman against SciPy span 8/16-bit ranges, independent/positive/negative relationships and tied values (absolute tolerance 1e-12). A separate analytic orthogonal-predictor fixture verifies signed standardized regression coefficients and their ratio. The frozen backend has passed a native synthetic OME-TIFF import and six-pair ROI analysis smoke test. These are engineering checks, not substitutes for the following release gates:

| Requirement | Current evidence | Remaining gate |
|---|---|---|
| Formula correctness | Analytic fixtures and SciPy correlation comparisons | Independent Fiji/Coloc 2 comparison using matched masks and threshold conventions |
| Acquisition validity | Metadata provenance and explicit scale confirmation | Check saturation, bleed-through, channel displacement and noise on representative acquisitions |
| Biological interpretation | No binding-probability or causal claim | Blinded positive and negative controls; registration sensitivity where calibration data are unavailable |
| Robust inference | Descriptive measures only | Spatially valid null models, uncertainty calibration and experiment-level replicate analysis |
| Reproducibility | Source hashes, ROI geometry, thresholds, native intensities, algorithm version exported | Versioned benchmark datasets, sample-specific methods reporting and independent review |

Reference guidance: [Dunn, Kamocka & McDonald, 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3074624/), [Fiji Coloc 2](https://imagej.net/plugins/coloc-2), and [reproducible microscopy methods reporting](https://www.nature.com/articles/s41592-021-01156-w). The Costes-style implementation has explicitly documented differences and must not be described as identical to Fiji or as implementing the Costes randomization significance test. Pixels, adjacent Z planes and multiple ROIs from one cell must not be presented as independent biological replicates.

## Proposed biological benchmark panel

The user proposed gamma-tubulin and pericentrin at centrosomes, with mitochondria as a contrasting compartment. Treat this as an experiment-specific hypothesis, not a guaranteed ground-truth label. Centrosomal gamma-tubulin/pericentrin co-enrichment is a candidate positive localization benchmark ([original study](https://pmc.ncbi.nlm.nih.gov/articles/PMC2132723/)). A distinct gamma-tubulin pool associated with mitochondria has also been reported ([original study](https://pmc.ncbi.nlm.nih.gov/articles/PMC6123723/)); therefore gamma-tubulin/MitoTracker must not be hard-coded as a universally negative control. Neither expected colocalization nor expected separation supplies a predetermined numerical correlation or proof of binding.

Use cell-line- and acquisition-specific control evidence, documented antibody specificity, single-label controls for bleed-through, and a separately established negative localization control. Synthetic perfectly correlated, separated, shifted and independent fields provide known numerical/spatial benchmarks but do not replace biological controls. Before publication validation, obtain representative source TIFFs and their condition, cell and independent-experiment identifiers; establish masks and exclusion rules before unblinded comparison. Compare matching masks and intensity conventions with independent microscopy software, test noise/background/threshold/channel-displacement sensitivity, then quantify uncertainty at the independent-experiment level. Acquisition limitations from missing registration/PSF calibration must remain explicit in any interpretation of proximity.

## 0.1.5 research-workspace verification

Linked source sections are tested against independently constructed XY/XZ/YZ slices, including orientation, native contrast conversion and invalid bounds. Cuboid tests check inclusive source indices, raw/processed sums, voxel counts, physical volumes and source identity. Spatial tests compare exhaustive null correlations with independent NumPy roll/correlation calculations, verify seed repeatability, exact-tail counts, undefined constant cases and explicit model selection. Sensitivity tests check matched thresholds and known subtraction effects. None establishes biological false-positive calibration.

Evidence tests use mocked provider responses for identifier restrictions, local authentication, academic gating, cache integrity/offline staleness, provenance, pathway parsing and partial failures. Live public-identifier smoke tests resolved TUBG1/PCNT, retrieved their STRING network edge and retrieved human TP53 KEGG memberships/names. These are service-connectivity checks, not validation of biological interpretation. No images or measurements were transmitted.

Browser checks on a generated 64×64×8 two-channel stack observed successful numeric references, raw/processed comparisons, a seeded spatial result and linked sections with a 32,768-voxel cuboid volume of 131.072 µm³ at 0.1×0.1×0.4 µm spacing. This small example does not establish large-stack performance. The source milestone does not include a new installer or native Windows/macOS packaging verification.

## 0.1.6 pathway diagrams and comparison documentation

KEGG diagram tests cover session authentication, academic-use gating, strict human pathway IDs, validated PNG responses, native dimensions, content hashes, cache reuse, missing offline entries and rejection of HTML responses. The interface test verifies no diagram request occurs until the user activates the pathway action, then checks the dialog, zoom and close behavior. A live browser check followed human TP53 identifier selection to the p53 signalling pathway (hsa04115), displayed its official 1305×775 PNG, and reopened the same diagram with offline-only caching enabled. This verifies access/display, not signalling activity or causal inference. The README and SOFTWARE_COMPARISON.md distinguish sourced capabilities, plugin variants, unassessed features and release-validation gaps across eight tools; no comparative performance or scientific-accuracy benchmark is claimed.


## Source milestone 0.1.7 — projects and experimental local assistant

Versioned local snapshots, source/metadata checks, revision conflicts, restored validation/3D workspace state, stale-callback isolation, a pinned local llama.cpp/Qwen3.5-4B integration, bounded read-only tools and response checks have engineering tests. These additions do not validate biological interpretation. Real local-model smoke tests identified a unit error in generated prose, leading to a qualitative-answer design with recorded numeric values displayed separately. See ASSISTANT_EVALUATION.md for observations and remaining gates. This source milestone does not change previously installed binaries or publish a new installer.


## Manual batch milestone 0.1.10

[Batch verification and remaining limits](BATCH_ANALYSIS.md#development-verification--17-october-2026) documents calibrated circle masks, independent manually reviewed image queues, shared interactive/batch calculation checks, cancellation/failure preservation and Excel read-back. The small synthetic workload and software tests do not substitute for independent Fiji/reference-image comparison or biological controls.


## UI and arithmetic follow-up 0.1.11

[Independent cuboid verification](CUBOID_VERIFICATION.md) reproduces the reported sample coefficient and identifies its empty RGB component. Tests separately cover direct TIFF decoding/cropping, metric-specific undefined reasons, movement/bounds submission, current-context assistant requests and optional offline inference. Model fluency and a successful request without a saved project do not establish scientific correctness. A general-question smoke answer overclaimed the effect of brightness alone on Pearson; the application-method context now states the conditions for affine invariance. No biological accuracy improvement is inferred from that prompt change.

The final 0.1.11 source run passed **109 backend tests and 44 frontend tests**, plus the UI production build. Live UI checks covered source-linked background help, preserved older ROI results after an import-quality-note update, moved cuboid bounds, the reported sample coefficient, explanations for zero-channel correlations, and general/current-image assistant requests without saving or online refresh. Missing-versus-undefined context and exact channel-label handling were corrected during those checks. Native installer qualification and biological/cross-software benchmarking remain outstanding.

## Rolling ball and XYZ size controls — 0.1.12

The full run passed **118 backend tests and 47 frontend tests**, plus TypeScript checking and the production UI build. Rolling-ball tests use a separate scalar geometry reference for 8/16-bit data including edges, analytic impulse curvature, constant backgrounds, unchanged source bytes, invalid settings, API preview/plane/provenance, and processed cuboid cropping. No additional dependency or model is introduced; SciPy evaluates the curved nonflat lower envelope. Details and a single full-resolution timing are in [preprocessing](PREPROCESSING.md).

Raw XYZ containment tests replace every outside-cuboid voxel with a bright value without changing summaries or pair metrics, test contributions at both included Z endpoints, and test single-slice selection within a stack. UI tests check smaller/larger sizes, boundary clamping and exact submitted coordinates. The live confocal sample was resized to 32 × 40 × 12 (X = 169–200, Y = 165–204, Z = 12–23), measured as 15,360 source voxels with calibrated volume 300.7936 µm³. The preparation comparison displayed the new rolling-ball recipe successfully. Existing biological, native installer and cross-software validation limits remain.

## Shared preview layout — 0.1.13

The preview is mounted above the workspace navigation and outside workspace visibility conditions. Separate preview mode and workspace selection preserve the current XY/3D view when moving between Image & ROI, 3D workspace, Validation, Molecular evidence, Batch analysis and Local assistant. Regression checks verify DOM order, preview identity, selected Z plane and drawing tool across all tabs, and a stateful volume-view stand-in across tab changes. The full frontend run passed **51 tests**. Live checks also confirm the sample remains displayed in Validation and that the 3D workspace tab does not force a preview-mode change. The production UI build passes; quantitative backend algorithms are unchanged.

### Numeric entry follow-up

Preprocessing fields now retain text while being edited, so deleting radius, ball height, Gaussian sigma or a channel offset leaves an empty input after blur. Empty active inputs disable Apply instead of becoming zero; the current applied recipe/preview stays unchanged. Valid entries are converted to numbers only for the applied recipe. Explicit sigma = 0 remains supported. Unused blank background fields do not prevent switching to another method. The complete frontend suite passes **53 tests**, and the production UI build passes. A live browser check confirmed all three reported fields were empty and Apply was disabled.

## Restoration, geometry and inference — 0.2.0

See [full definitions and measured limitations](RESTORATION_AND_INFERENCE.md), [direct Coloc_2 benchmark](COLOC2_BENCHMARK.json), [held-out synthetic N2V test](N2V_SYNTHETIC_BENCHMARK.json), [Gaussian posterior simulation](INFERENCE_SYNTHETIC_BENCHMARK.json), and [native 2048² four-channel stack workload](LARGE_STACK_BENCHMARK.json). The workload decoded 512 MiB across 16 Z planes and checked exact source cuboid sums, calibrated viewing, segmentation and full-plane processing diagnostics. It is one synthetic source-service test, not native Windows or real acquisition validation.

New tests cover tensor-only model export/import, genuine training/tiled prediction, matched-source float artifacts, residual/QC values, Richardson–Lucy agreement with an independent library, known calibrated 3D masks, inclusive containment, proximity, radial shell counts, experiment/cell aggregation, paired-design rejection, analytic posterior parameters, multiple-comparison adjustment, project-archive integrity/path rejection and separate recovery persistence. Component tests cover restoration assumptions, shared-cuboid requests, stale-response protection and snapshot dimension/source preservation. Live visual checks remain blocked by browser access policy in this run.

Final local checks for this source milestone: **132 backend tests, 59 interface tests, production UI build passed**. The signed application bundle’s service is checked separately from source execution. See PACKAGED_RUNTIME_BENCHMARK.json for the exact scope; visual and biological validation are not implied.

## 0.2.1 scope change and layout

Noise2Void/RL execution tests and dependencies were removed with those features. Current checks cover absence of their routes, rejection of retired processing in new calculations, lossless historical archive/recovery retention, recalculation-copy migration, supported Gaussian/background recipes, separate workspace visibility, XY zoom bounds/aspect ratio and persistence of source ROI coordinates. Previous runtime benchmark files describe historical 0.2.0 builds.

XY gesture checks (0.2.1): component tests verify pinch/wheel event consumption, pointer anchoring, bounded zoom, drag/draw separation, and unchanged source SVG coordinates. Browser wheel zoom changed the fitted scale from 100% to 149%; dragging moved the scroll position from 66.5 to 116.5 pixels without adding an ROI. These are display interaction checks, not biological validation.

## Source 0.2.2 — channel LUTs and documentation

Display-only linear LUTs now apply to the selected single-image XY, linked-section, preparation and 3D previews. Project/recovery workspaces and snapshot details preserve choices. Endpoint tests check red/blue pixel outputs, invalid LUT rejection, unchanged native TIFF planes/source identity and identical quantitative ROI results before/after display requests. Frontend tests cover channel selection, preview/processing request propagation, cross-tab persistence, saved workspace state and reset. Browser checks on the existing Fiji flybrain sample confirmed magenta/cyan XY display, live 3D recolouring and successful XY/3D PNG capture. The sample is flagged as RGB; it is used for display behaviour, not quantitative biological validation.

README is shortened; MANUAL.md documents current workflows, metric conventions, interpretation, glossary and references. New model/napari assessments are literature/integration proposals, not model trials or implemented viewer roadmap features. No model was downloaded or replaced and no new installer was built for this source milestone.

## 0.2.3 local sample and Workspace verification — 18 October 2026

Four user-provided TIFFs were tested locally without publishing their pixels, embedded acquisition metadata, hashes or numerical measurements. Two are 2048×2048 multichannel Z stacks (four channels/eighteen planes and three channels/four planes); two contain a single grayscale plane. The latter retain an inherited ImageJ Info acquisition block describing more channels/planes than are actually stored. The importer now warns about this mismatch and retains actual TIFF geometry. It does not reconstruct missing channels or silently use the original acquisition dimensions. Synthetic regression cases cover both mismatched and matching Info blocks.

The opt-in `scripts/validation/check_local_samples.py` writes its full report under ignored `local-samples/` by default. It uses disposable source symlinks to avoid duplicating large TIFFs and exercises stored-image APIs, not upload copying. Checks compare first/middle/last native planes across every channel against independent TIFF page indexing, decode default/selected-LUT and rolling-ball/Gaussian preview PNGs, compare defined ROI Pearson/Spearman values with SciPy, compare inclusive cuboid counts/all-channel sums with independent source-page crops, and check linked sections/volume payloads. Single-channel correlation and single-plane volume requests are rejected explicitly. Original source hashes are unchanged after all checks. Geometric-center ROIs and arbitrary preparation settings serve only as technical fixtures; they are not reviewed biological masks or validated scientific recipes. Channel-to-protein identities and export history remain pending clarification. No control-separation, binding, causal, population or publication claim follows from these checks.

Project save/open/archive/recovery controls now reside inside the Workspace sidebar. Component checks assert containment and removal of the old top bars; existing project/preview tests remain. The new four-colour theme affects UI chrome only. The last built installer remains a separately identified earlier artifact; this source milestone does not rebuild/publish it.
