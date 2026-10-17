# OrganelleScope

<img width="1408" height="768" alt="Gemini_Generated_Image_dqzhhvdqzhhvdqzh" src="https://github.com/user-attachments/assets/83f9f9c1-0c57-4a9f-b3f3-c910ade41f6e" />


A local desktop microscopy workbench for calibrated image inspection, ROI measurements, colocalization, 3D analysis and traceable biological interpretation. It brings together the Probabilistic Colocalization Estimator and Quick IF Line Profiler.

**Research development source 0.2.2.** Numerical tests do not establish biological validity or publication readiness. Windows 11 x64 and Apple Silicon macOS are the deployment targets; native platform qualification remains incomplete. Installed builds can lag this source.

## Main features

- TIFF / OME-TIFF / ImageJ TIFF, native 8/16-bit data, static images/Z stacks and up to four channels, with metadata review and physical calibration.
- Persistent XY/3D preview, per-channel LUTs, trackpad zoom/panning, linked sections and PNG snapshots with display provenance.
- Circular/polygonal ROIs, physical circle diameters, line profiles, FWHM and defined Pearson/Spearman/Manders measurements.
- Background subtraction and optional Gaussian smoothing, matched-contrast previews and processing diagnostics. Noise2Void and deconvolution have been removed.
- Full-resolution cuboids, inspectable threshold masks/objects, image-based proximity and radial enrichment.
- Reviewed per-image batches, Excel/JSON export and experiment-level resampling with optional explicit Gaussian MLE/Bayesian models.
- Optional human STRING/academic KEGG lookups and pathway diagrams; a supervised local Gemma assistant for recorded results and evidence.
- Local versioned projects, portable archives, recovery state and source/settings/evidence provenance.

## Start here

Read the **[complete manual](MANUAL.md)** for installation, step-by-step use, every current workspace, formulas, interpretation, limits, troubleshooting, glossary and references.

Open a TIFF, confirm channels/axes/calibration, inspect the image and draw ROIs. Select analysis settings explicitly, calculate and export the full results. Saving is optional for asking the assistant; model setup is separate from image analysis. Neither overlap nor a rendered volume establishes molecular binding or super-resolution.

## Documentation

| Guide | Contents |
|---|---|
| [Manual](MANUAL.md) | User guide and scientific interpretation |
| [Software comparison](docs/SOFTWARE_COMPARISON.md) | napari, QuPath, CellProfiler, Fiji JaCoP/Coloc 2, Icy and Imaris |
| [Model decisions](README_MODEL_DECISIONS.md) / [candidate assessment](docs/MODEL_SELECTION.md) | Why Gemma remains; GPT-OSS, Llama Vision and optional vision candidates |
| [napari-inspired roadmap](docs/NAPARI_INSPIRED_ROADMAP.md) | Prioritized proposals, clearly separated from implemented LUTs |
| [Validation](docs/VALIDATION.md) / [release readiness](docs/RELEASE_READINESS.md) | Numerical evidence and outstanding qualification |

## Development and downloads

See [development setup](MANUAL.md#57-development-setup). GitHub Actions can build development installers; local output is in `release/` and is excluded from Git. Installers belong in GitHub Releases or Actions artifacts, not the Packages registry. See the [verified build record](docs/BUILD_VERIFICATION.json); this source update does not publish a new installer.

## Licensing

New application licensing remains undecided. Predecessor PolyForm Noncommercial terms and [third-party notices](third_party/NOTICE.md) remain relevant. Model/database terms are separate; KEGG access is academic-only in this application. Public source visibility is not an additional license grant. No experimental images, credentials or model weights belong in Git.
