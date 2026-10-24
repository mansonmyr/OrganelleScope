# OrganelleScope

<img width="1408" height="768" alt="Gemini_Generated_Image_dqzhhvdqzhhvdqzh" src="https://github.com/user-attachments/assets/83f9f9c1-0c57-4a9f-b3f3-c910ade41f6e" />


A local desktop microscopy workbench for calibrated image inspection, ROI measurements, colocalization, 3D analysis and traceable biological interpretation. It brings together the Probabilistic Colocalization Estimator and Quick IF Line Profiler.

**Source version 1.0.8 — local research workbench.** Supports Apple Silicon macOS and Windows 11 x64. Published installer versions and qualification records are listed separately on Releases. Release gates cover numerical tests, frozen analysis workflows, repeated native cold/warm startup, shutdown, large-stack/batch workloads and exact installer checksums. Scientific scope and comparison records are documented in the [manual](MANUAL.md) and [verification status](docs/VALIDATION.md).

## Main features

- TIFF / OME-TIFF / ImageJ TIFF, native 8/16-bit data, static images/Z stacks and up to four channels, with metadata review, physical calibration and acquisition sampling/ceiling checks.
- Persistent native-range XY/3D preview, optional automatic contrast, editable channel names, signal checks, per-channel LUTs, trackpad zoom/panning, linked sections and PNG snapshots with display provenance.
- Circular/polygonal ROIs, physical circle diameters, line profiles and Pearson/Spearman/Manders measurements, with per-ROI raw ceiling counts, threshold-occupancy diagnostics and withholding of widths affected by raw clipping.
- Background subtraction, optional Gaussian smoothing, matched-contrast previews and ROI background variation. The curved-kernel lower envelope is identified separately from morphological opening.
- Full-resolution cuboids, threshold masks, bidirectional calibrated voxel-centre proximity and radial enrichment, with ROI/threshold/cuboid sensitivity sweeps.
- Reviewed per-image batches with channel editing, design checks and failed-item recovery, Excel/JSON export and experiment-level resampling with optional explicit Gaussian MLE/Bayesian models.
- Optional human STRING/academic KEGG lookups and pathway diagrams; a supervised local Gemma assistant with separate claim support and question-coverage reviews.
- Source-plane memory release during reduced 3D preview generation, cancellable ROI analysis with progress, portable analysis-review reports linking engine results to embedded ROI previews, and source/settings/evidence provenance.
- Workspace sidebar project controls, portable archives, recovery state and preserved ROI-report history with original algorithm/settings metadata.

## Start here

Read the **[complete manual](MANUAL.md)** for installation, step-by-step use, every current workspace, formulas, interpretation, limits, troubleshooting, glossary and references.

Open a TIFF, confirm channels/axes/calibration, inspect the image and draw ROIs. Select analysis settings explicitly, calculate and export the full results. Saving is optional for asking the assistant; model setup is separate from image analysis. Neither overlap nor a rendered volume establishes molecular binding or super-resolution.

## Application scope and limits

- Conventional microscopy retains its acquisition resolution: rendering and interpolation do not create validated super-resolution or prove molecular binding.
- Calibration, channel identities, ROI selection, thresholds and independent experimental units must be checked for each study. Owner-reviewed sample regions and numerical comparisons support specific workflows; they do not establish population-level biological accuracy.
- Gemma provides optional drafts for human review. Source checks can miss unsupported claims; recorded measurements remain the quantitative record.
- TIFF images/static stacks up to four channels are supported. Time-lapse, Noise2Void and deconvolution are outside the current feature set. Large-stack capacity depends on available memory.

Small-sample comparisons show an estimation-only mode when an exact two-sided permutation test cannot attain 0.05. Sample SD and optional Gaussian MLE SD are distinguished. Exploratory percentile intervals are off by default because nominal coverage is not established. See the [manual](MANUAL.md) for assumptions and the [synthetic assessment](docs/validation/SMALL_SAMPLE_COVERAGE_1.0.8.json) for the tested model.

## Documentation

| Guide | Contents |
|---|---|
| [Manual](MANUAL.md) | User guide and scientific interpretation |
| [Software comparison](docs/SOFTWARE_COMPARISON.md) | napari, QuPath, CellProfiler, Fiji JaCoP/Coloc 2, Icy and Imaris |
| [Model decisions](README_MODEL_DECISIONS.md) | Why Gemma remains; GPT-OSS, Llama Vision and optional vision candidates |
| [Validation](docs/VALIDATION.md) | Release checks and scientific scope |

## Install and upgrade

Download Windows x64 or Apple Silicon macOS installers from **[Releases](https://github.com/mansonmyr/OrganelleScope/releases)**. Only the `.dmg` (Apple Silicon Mac) or `.exe` (Windows x64) is needed for installation. Other assets provide checksums, licence notices and verification records. A new account starts with no imported images, projects, batch history or recovery workspace; upgrades and reinstalls preserve that account’s existing local work. Each release includes checksums and platform verification records. Stable tags are published only when both platform qualification gates pass. Save/export projects before upgrading; replacing the application preserves its separate local research data and verified model storage. Previous releases remain available for rollback. The installed application includes its local inference runtime and sets up Gemma automatically with a one-time 6.98 GB download. Setup can be paused/resumed; image analysis remains available. After setup the assistant runs offline. macOS is ad-hoc signed and not notarized; Windows has no publisher certificate.

Use the [manual](MANUAL.md) for source setup, diagnostics and reporting. The optional local AI assistant generates drafts with source checks; it does not verify biological truth. Recorded analysis summaries remain available without the model or when a draft is withheld. Cite the exact release using [CITATION.cff](CITATION.cff), alongside original methods. Confirm stored-channel marker identities before biological interpretation; filenames and dye names are not ground truth.

## Python-only numerical replay

No Node.js, Electron, model or graphical session is required:

```sh
python -m venv .venv
# Activate the environment using your platform's normal command.
python -m pip install ./backend
python -m organelle_scope.cli demo --output replay/demo.json
```

The demo reproduces a closed-form reference table: perfect/negative correlation,
average ranks with ties, directional intensity fractions, and anisotropic two-point
distances. To replay a shared microscopy window from the manuscript supplement:

```sh
python -m organelle_scope.cli roi --data sample-feature-results/data --sample P5 --mode costes --output replay/P5.json
```

That command checks the TIFF hash and uses explicit ZCYX geometry and spacing from
`manifest.json`; it does not infer channel identity or acquisition calibration.
The `proximity` subcommand accepts matching binary ZYX TIFF masks; see `--help`.
The paper's supplement contains microscopy windows and additional assessment
scripts. A release of the desktop app is not a substitute for the exact submitted
manuscript, data manifest and reproduction archive.

## Licensing

Author-owned OrganelleScope code, including the incorporated portions of Quick IF Line Profiler and Probabilistic Colocalization Estimator, is distributed under [GNU GPLv3](LICENSE). Kai Hong Ooi, sole rights holder of those incorporated portions, authorizes this distribution under GPLv3. Historical predecessor licence texts are retained for attribution and provenance; they do not add a noncommercial restriction to these relicensed portions. Third-party dependencies retain their own licences; see [component notices](third_party/NOTICE.md). Model/database terms are separate. KEGG access is academic-only in this application. Research images, credentials and model weights are not included in the repository.
