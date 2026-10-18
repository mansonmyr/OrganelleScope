# OrganelleScope

<img width="1408" height="768" alt="Gemini_Generated_Image_dqzhhvdqzhhvdqzh" src="https://github.com/user-attachments/assets/83f9f9c1-0c57-4a9f-b3f3-c910ade41f6e" />


A local desktop microscopy workbench for calibrated image inspection, ROI measurements, colocalization, 3D analysis and traceable biological interpretation. It brings together the Probabilistic Colocalization Estimator and Quick IF Line Profiler.

**Version 1.0.0 — local research workbench.** Supports Apple Silicon macOS and Windows 11 x64. Release gates cover numerical tests, frozen analysis workflows, repeated native cold/warm startup, shutdown, large-stack/batch workloads and exact installer checksums. Scientific scope and comparison records are documented in the [manual](MANUAL.md) and [verification status](docs/VALIDATION.md).

## Main features

- TIFF / OME-TIFF / ImageJ TIFF, native 8/16-bit data, static images/Z stacks and up to four channels, with metadata review and physical calibration.
- Persistent native-range XY/3D preview, optional automatic contrast, editable channel names, signal checks, per-channel LUTs, trackpad zoom/panning, linked sections and PNG snapshots with display provenance.
- Circular/polygonal ROIs, physical circle diameters, line profiles, FWHM and defined Pearson/Spearman/Manders measurements.
- Background subtraction and optional Gaussian smoothing, matched-contrast previews and processing diagnostics. Noise2Void and deconvolution have been removed.
- Full-resolution cuboids, inspectable threshold masks/objects, image-based proximity and radial enrichment.
- Reviewed per-image batches with channel editing and design checks, Excel/JSON export and experiment-level resampling with optional explicit Gaussian MLE/Bayesian models.
- Optional human STRING/academic KEGG lookups and pathway diagrams; a supervised local Gemma assistant for recorded results and evidence.
- Workspace sidebar project controls, portable archives, recovery state and source/settings/evidence provenance.

## Start here

Read the **[complete manual](MANUAL.md)** for installation, step-by-step use, every current workspace, formulas, interpretation, limits, troubleshooting, glossary and references.

Open a TIFF, confirm channels/axes/calibration, inspect the image and draw ROIs. Select analysis settings explicitly, calculate and export the full results. Saving is optional for asking the assistant; model setup is separate from image analysis. Neither overlap nor a rendered volume establishes molecular binding or super-resolution.

## Documentation

| Guide | Contents |
|---|---|
| [Manual](MANUAL.md) | User guide and scientific interpretation |
| [Software comparison](docs/SOFTWARE_COMPARISON.md) | napari, QuPath, CellProfiler, Fiji JaCoP/Coloc 2, Icy and Imaris |
| [Model decisions](README_MODEL_DECISIONS.md) | Why Gemma remains; GPT-OSS, Llama Vision and optional vision candidates |
| [Validation](docs/VALIDATION.md) | Numerical evidence and outstanding qualification |

## Install and upgrade

Download Windows x64 or Apple Silicon macOS installers from **[Releases](https://github.com/mansonmyr/OrganelleScope/releases)**. Each release includes checksums and platform verification records. Stable tags are published only when both platform qualification gates pass. Save/export projects before upgrading; replacing the application preserves its separate local research data and verified model storage. Previous releases remain available for rollback. The installed application includes its local inference runtime and sets up Gemma automatically with a one-time 6.98 GB download. Setup can be paused/resumed; image analysis remains available. After setup the assistant runs offline. macOS is ad-hoc signed and not notarized; Windows has no publisher certificate.

Use the [manual](MANUAL.md) for source setup, diagnostics and reporting. The optional local AI assistant generates drafts with source checks; it does not verify biological truth. Recorded analysis summaries remain available without the model or when a draft is withheld. Cite the exact release using [CITATION.cff](CITATION.cff), alongside original methods. Confirm stored-channel marker identities before biological interpretation; filenames and dye names are not ground truth.

## Licensing

The repository includes the user-provided [GNU GPLv3 license](LICENSE). Retained predecessor PolyForm Noncommercial notices and [third-party terms](third_party/NOTICE.md) must also be considered; adding a repository license does not itself relicense other rights holders' components. Model/database terms are separate; KEGG access is academic-only in this application. Public source visibility is not an additional license grant. No experimental images, credentials or model weights belong in Git.
