# OrganelleScope

<img width="1408" height="768" alt="Gemini_Generated_Image_dqzhhvdqzhhvdqzh" src="https://github.com/user-attachments/assets/83f9f9c1-0c57-4a9f-b3f3-c910ade41f6e" />


A local desktop microscopy workbench for calibrated image inspection, ROI measurements, colocalization, 3D analysis and traceable biological interpretation. It brings together the Probabilistic Colocalization Estimator and Quick IF Line Profiler.

**Research development source 0.2.6.** Numerical tests do not establish biological validity or publication readiness. Windows 11 x64 and Apple Silicon macOS are the deployment targets; native platform qualification remains incomplete. Installed builds can lag this source.

## Main features

- TIFF / OME-TIFF / ImageJ TIFF, native 8/16-bit data, static images/Z stacks and up to four channels, with metadata review and physical calibration.
- Persistent native-range XY/3D preview, optional automatic contrast, editable channel names, signal checks, per-channel LUTs, trackpad zoom/panning, linked sections and PNG snapshots with display provenance.
- Circular/polygonal ROIs, physical circle diameters, line profiles, FWHM and defined Pearson/Spearman/Manders measurements.
- Background subtraction and optional Gaussian smoothing, matched-contrast previews and processing diagnostics. Noise2Void and deconvolution have been removed.
- Full-resolution cuboids, inspectable threshold masks/objects, image-based proximity and radial enrichment.
- Reviewed per-image batches, Excel/JSON export and experiment-level resampling with optional explicit Gaussian MLE/Bayesian models.
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

## Development and downloads

Download Windows x64 or Apple Silicon macOS installers from **[Releases](https://github.com/mansonmyr/OrganelleScope/releases)**. Each release candidate includes checksums and platform verification records. The installed application includes its local inference runtime and sets up Gemma automatically with a one-time 6.98 GB download. Setup can be paused/resumed; image analysis remains available. After setup the assistant runs offline. macOS is ad-hoc signed and not notarized; Windows has no publisher certificate.

See [source setup and publishing](docs/DEVELOPMENT.md). Native installation checks and biological validation remain incomplete; see [verification status](docs/VALIDATION.md).

## Licensing

The repository includes the user-provided [GNU GPLv3 license](LICENSE). Retained predecessor PolyForm Noncommercial notices and [third-party terms](third_party/NOTICE.md) must also be considered; adding a repository license does not itself relicense other rights holders' components. Model/database terms are separate; KEGG access is academic-only in this application. Public source visibility is not an additional license grant. No experimental images, credentials or model weights belong in Git.
