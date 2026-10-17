# OrganelleScope

A desktop microscopy workbench bringing together the Probabilistic Colocalization Estimator and Quick IF Line Profiler, with image measurements, processing sensitivity, calibrated 3D inspection and molecular evidence in one local workflow.

**Source milestone 0.1.9 — research software in development. Numerical checks and working features do not constitute biological or publication validation. Installed binaries may lag the source; this milestone does not publish a new installer.**

## Current functionality

| Area | Implemented | Current boundary |
| --- | --- | --- |
| Image import | TIFF, OME-TIFF and ImageJ TIFF; 8/16-bit; up to four channels; axes/calibration provenance and manual correction | Static images/stacks; unsupported layouts fail explicitly; no time-lapse analysis |
| ROI and profiles | Circular/polygonal XY ROIs per Z plane; calibrated line profiles and single-peak FWHM | Selected lines/ROIs are retained in local projects; batch workflows remain pending |
| Colocalization | Pearson, Spearman, overlap and Manders measures; per-channel summaries and standardized regression | No molecular-binding probability; formulas/threshold conventions must be matched before comparing software |
| Preprocessing | Constant per-channel or square-opening background subtraction; optional Gaussian smoothing; raw/processed measurement selection and matched-contrast comparison | Noise2Void, deconvolution and learned reconstruction are pending |
| Statistical controls | Independent numeric references, processing sensitivity and seeded whole-plane toroidal shifts for one ROI/channel pair | Stationarity-dependent, unadjusted spatial control; no experiment-level inference or general significance certification |
| 3D inspection | All-channel volume rendering, physical/voxel-space labeling, linked XY/XZ/YZ sections and display-only Z stretch | Downsampled rendering is separate from measurement; no claim of super-resolution |
| 3D measurement | Inclusive full-resolution cuboid summaries, calibrated region volume and channel associations | Up to 500,000 voxels per region; cuboid volume is not segmented organelle volume |
| Molecular evidence | Human STRING identifier selection/association networks and academic KEGG gene/pathway lookup; on-demand KEGG pathway diagrams with zoom and provenance | Identifier/species queries only; reference maps do not show experimentally inferred activation or knockdown effects |
| Reproducibility | Source SHA-256, calibration, processing recipes/versions, ROI requests, seeds, evidence dates/hashes and JSON reports | Versioned local projects restore workspace settings, ROI/3D/validation reports and evidence; manual save, one image per project; portable archives/autosave pending |
| Local assistant | Gemma 4 12B Instruct official QAT Q4_0 via owned llama.cpp; saved-project inspection, deterministic reference tools and bounded STRING/KEGG refresh with visible tool records | Experimental; qualitative drafts with recorded numeric values shown separately; model/runtime setup separate; native Windows and biological interpretation validation pending |
| Desktop distribution | Electron/local Python service; macOS ARM64 and Windows x64 packaging configuration | Development distribution; no Developer ID notarization, production certification or bundled LLM |

Methods: [ROI statistics](docs/ROI_STATISTICS.md), [preprocessing](docs/PREPROCESSING.md), [research workspaces and evidence](docs/RESEARCH_WORKSPACES.md), [validation status](docs/VALIDATION.md).

## Functional comparison with other applications

Reviewed **16 October 2026** against the primary documentation linked below. This is a capability and workflow comparison, not an accuracy, speed or usability benchmark. Host applications, bundled modules and optional plugins are identified separately. A feature not described in the reviewed sources is not proof that no extension can provide it. Versions, enabled plugins and commercial packages matter.

| Application / component | Main workflow | Colocalization and quantitative analysis | 3D and object analysis | Automation / reproducibility | Fit relative to OrganelleScope |
| --- | --- | --- | --- | --- | --- |
| **OrganelleScope 0.1.9 source** | Guided local fluorescence inspection, measurements and biological context | Built-in XY/cuboid intensity metrics, profiles, processing sensitivity and a conditional translation control | Volume preview, linked sections and cuboids; organelle segmentation pending | Versioned local projects and source/recipe/seed/evidence records; bounded experimental local assistant; batch jobs pending | Combines these steps in one interface; scientific and production validation remain incomplete |
| **[napari](https://napari.org/stable/getting_started/quick_start.html)** | Extensible multidimensional image viewer and annotation platform | Analysis supplied through Python and domain-specific plugins; capabilities depend on the selected tools | Native n-dimensional layers, 3D visualization and annotations | Python API and plugins | Stronger general-purpose viewer ecosystem; compare a specified plugin configuration rather than treating the viewer as a fixed colocalization package |
| **[QuPath](https://github.com/qupath/qupath/blob/main/README.md)** / [multiplex analysis](https://qupath.readthedocs.io/en/latest/docs/tutorials/multiplex_analysis.html) | Large-image, whole-slide, tissue/cell and multiplex analysis | Cell/object intensity measurements and classification; custom workflows through scripting/extensions | Rich tissue/object workflows; the reviewed documentation focuses on these rather than a confocal volume-rendering suite | Projects, scripting and extensibility | Stronger established tissue-analysis and project workflows; different primary focus from subcellular stack colocalization |
| **[CellProfiler](https://cellprofiler.org/introduction)** / [MeasureColocalization](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.2.8/modules/measurement.html#measurecolocalization) | Reusable image-analysis pipelines and high-content measurements | Dedicated image/object colocalization module, including 2D and 3D support | Segmentation and object measurements; module-specific dimensional support | Configurable pipelines and export workflows | Stronger established automated analysis; assess the chosen modules/settings rather than assuming all metrics are equivalent |
| **Fiji/ImageJ + [JaCoP](https://imagej.net/imaging/colocalization-analysis)** | Dedicated colocalization plugin within ImageJ | Pearson, Manders/overlap, Li/Van Steensel approaches, Costes tools and object-based options | Stack/object capabilities depend on the JaCoP variant and settings; host supplies additional tools | ImageJ workflows; reproducibility depends on recording plugin version, masks and parameters | A broader established colocalization toolbox; classic JaCoP and BIOP variants must be distinguished in benchmarks |
| **Fiji/ImageJ + [Coloc 2](https://imagej.net/plugins/coloc-2)** | Pixel-intensity colocalization with scatterplots and reports | Pearson, Manders, Costes, Li, automatic thresholds and significance testing | Z-stack support; Coloc 2 explicitly does not provide object-based colocalization | Host workflows and numerical/report output | A priority independent benchmark. OrganelleScope's Costes-style thresholds and toroidal test are not claimed to reproduce Coloc 2 |
| **[Icy](https://icy.bioimageanalysis.org/)** + [ColocalizationStudio protocol](https://icy.bioimageanalysis.org/protocol/spot-detection-and-colocalization-object-analysis/) | Extensible bioimage processing with reusable protocols | Documented spot-detection/object-colocalization workflow; additional analysis depends on plugins/protocols | Detection/ROI workflows depend on the chosen components | Visual protocols, plugins and scripts | A relevant comparator for future object/spot analysis; matching methods and segmentation settings is essential |
| **[Imaris Essentials / Coloc](https://imaris.oxinst.com/products/imaris-essentials)** | Commercial interactive 3D microscopy visualization and analysis | Colocalization/co-distribution analysis within the Imaris product ecosystem | Volume/surface rendering, object distances and overlaps | Package-dependent analysis workflows and reporting | A stronger established 3D-analysis comparator; current OrganelleScope cuboids do not replace surface segmentation or object-distance workflows |

OrganelleScope's present emphasis is the connection between calibrated images, explicit measurement/processing choices and traceable STRING/KEGG context. This is an integration goal, not a claim that individual methods are unique or outperform existing tools. No exhaustive plugin-market survey or head-to-head validation has been performed. See the [detailed comparison and release-readiness criteria](docs/SOFTWARE_COMPARISON.md).

## KEGG pathway diagrams

1. Open **Molecular evidence**, select **KEGG**, and indicate academic research use.
2. Enter a human gene symbol (for example `TP53`), find candidates, and explicitly select the correct gene.
3. Retrieve its pathway memberships, then choose **View diagram** beside a pathway.
4. The official human KEGG PNG opens in a zoomable, scrollable dialog. The interactive KEGG website remains available through a source link.

Diagrams download only when requested. They share the bounded local evidence cache and can be reopened in **Offline only** mode after a successful fetch. No KEGG diagrams or database dumps are included in the repository/installer. Retrieval time, source URL and image hash accompany the evidence export; image colours are KEGG reference annotations, not measured signalling activity. Access requires an available provider or a matching cached result. [KEGG API documentation and academic-use restriction](https://www.kegg.jp/kegg/rest/), [image endpoint](https://www.kegg.jp/kegg/rest/keggapi.html).

## Next development priorities

1. **Project hardening and batch execution:** portable archives, autosave/recovery, multi-image experiments, cancellation and large-data workflows. Manual local project snapshots are now implemented.
2. **Independent scientific benchmarking:** matched JaCoP/Coloc 2/CellProfiler masks and threshold conventions; known controls, channel-registration sensitivity and false-positive calibration.
3. **Organelle segmentation and spatial measurements:** inspectable 3D masks, surfaces, enrichment and distances with explicit calibration/resolution limitations.
4. **Experiment-level inference:** condition/cell/experiment identifiers, effect sizes, confidence intervals and appropriate multiplicity control.
5. **Noise2Void/restoration and assistant evaluation:** validated restoration models, residual/measurement-bias checks; curated biological/tool/citation tests for the experimental local assistant.
6. **Release hardening:** native platform/large-stack tests, signing/notarization when credentials are available, installer releases and the marketing site.

The remaining capabilities listed above are planned; existing manual projects and the experimental local assistant are described separately below. No conversion of conventional microscopy into experimentally verified super-resolution data or inferred molecular binding is claimed. See the [development plan](docs/DEVELOPMENT_PLAN.md).

## Local projects and assistant

Use **Save project** to retain the imported source association, calibration, analysis settings, ROIs, 3D/validation reports and molecular evidence. Reopen from **Open saved project**. Save before switching images or quitting. This is one local image per project; portable archives, autosave and batch runs are not yet implemented.

The **Local assistant** reads the last saved revision and uses Gemma 4 12B Instruct QAT Q4_0 locally. Numeric values are displayed directly from saved engine results, alongside a qualitative AI draft and an inspectable tool record. Model/runtime files are a separate, explicit development download (about 6.99 GB total), not a cloud API or part of the current installer. After a successful inference, the app removes known retired model weights and temporary evaluation files; scientific data remains intact. See [setup, privacy and limitations](docs/LOCAL_ASSISTANT.md) and [evaluation](docs/ASSISTANT_EVALUATION.md).

## Development setup

Requires Python 3.11+ and Node.js 24. The planned user-facing installer will bundle its runtimes; these steps are for contributors.

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e 'backend[test]'
npm ci
npm ci --prefix frontend
```

On Windows use `backend\.venv\Scripts\python.exe`. Set `ORGANELLESCOPE_PYTHON` to the interpreter if it is not on PATH.

To start the browser development workspace and local backend:

```sh
ORGANELLESCOPE_PYTHON=backend/.venv/bin/python npm run dev
```

The development workspace is at `http://127.0.0.1:5173`. It uses a fixed **development-only** local token. Packaged desktop sessions generate a fresh random token. The service binds only to localhost, does not use cookie authentication, and requires the session header for image operations.

For the actual desktop workspace:

```sh
npm run build:ui
ORGANELLESCOPE_PYTHON=backend/.venv/bin/python npm run desktop
```

Use an absolute interpreter path if launching outside the repository. Imported images are copied to local application storage; originals are not modified. Development-mode imports live in `.dev-images/`, which is excluded from Git. Only open trusted TIFF files in this early build. Supported page layouts are explicit; unsupported layouts fail rather than load a misleading subset.

## Checks

```sh
backend/.venv/bin/python -m pytest backend/tests -q
npm test --prefix frontend
npm run build:ui
```

Synthetic tests cover basic import/calibration correctness and profile regressions. They do not establish biological validity, reconstruction fidelity, real-data performance or clinical suitability.

## Packaging

`npm run package` builds the UI and a PyInstaller backend, then packages with Electron Builder. Install PyInstaller in the selected Python environment first. Initial targets are macOS ARM64 and Windows x64; Windows ARM and native GPU support require further evaluation. The GitHub packaging workflow runs manually or on explicit `v*-dev*` tags and generates unsigned development artifacts, not a complete production release. No LLM or restoration weights are bundled at this stage.

## Sources and license status

The original repositories remain independent and have been backed up outside this repository. See [migration notes](docs/MIGRATION.md) and [third-party notices](third_party/NOTICE.md). The original projects use PolyForm Noncommercial 1.0.0. A final license for newly written OrganelleScope code has not been chosen; public availability alone does not grant an additional license.

No experimental TIFFs, credentials, model weights, or local environments belong in this repository.

## ROI statistics

Choose Circular ROI or Polygonal ROI from the drawing tool, draw one or more regions, select the threshold method, and press **Calculate ROI statistics**. The line profiler remains a separate drawing tool. ROIs use pixel-center coordinates; circular masks are circular in XY pixel coordinates. Measurements use the explicitly selected raw or processed intensities, independently for each ROI on its recorded Z plane; raw is the default. ROI area uses confirmed X/Y scale. Deleting or adding an ROI or changing analysis settings clears the displayed results until recalculation. The last successfully calculated analysis is restored when reopening a saved import. Unsaved edits do not replace it.

See [ROI measurement definitions](docs/ROI_STATISTICS.md) for formulas and limitations. No probability of molecular binding, calibrated significance or nanoscale resolution is inferred from these descriptive measurements.

## macOS development installation

Version 0.1.2 adds explicit ad-hoc development signing of the Mac app and its bundled analysis executable, plus strict signature checks before producing an installer. This is not Apple Developer ID signing or notarization. Mac development builds may still require an app-specific approval in **System Settings → Privacy & Security → Open Anyway** after attempting to open the app. See [Apple's instructions](https://support.apple.com/en-us/102445). A successful signature check is not a malware or scientific-validation certificate.

If a 0.1.1 installer reports that the app is damaged, replace it with the rebuilt 0.1.2 app rather than disabling Gatekeeper globally. Drag OrganelleScope from the new DMG into Applications and choose Replace. Imported images and analyses are stored separately in the app's user-data directory. The signing hooks clean only FinderInfo/ResourceFork metadata in generated build output and do not remove quarantine from installed apps.

A local packaging run writes installers into `release/` (excluded from Git). CI installers remain available as Actions artifacts until attached to a GitHub Release. Publication-ready Mac distribution requires a Developer ID certificate and notarization configured separately; these credentials are not present in the project.
