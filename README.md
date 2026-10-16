# OrganelleScope

A desktop microscopy workbench in development, bringing together the Probabilistic Colocalization Estimator and Quick IF Line Profiler.

**Current milestone: metadata, calibrated viewing, source line profiles, and per-plane ROI statistics. This is a development build, not a validated scientific release.**

## Available now

- TIFF, OME-TIFF and ImageJ TIFF inspection with source bit depth, channel names, shape, axis order and calibration provenance.
- Explicit correction of ambiguous axes; no automatic disposal of Z planes or time points.
- An information popup explaining physical calibration, Z step, sampling and optical resolution.
- Fiji escaped micrometre units are recognized automatically, and existing imports are refreshed.
- An explicitly labeled voxel-space preview is available when physical spacing is unknown.
- Conflicting physical-scale metadata blocks physical interpretation until corrected.
- Page-wise viewing of supported uint8/uint16 layouts, up to four channels.
- Native-intensity line profiles on a selected XY plane, calibrated for unequal X/Y spacing.
- Circular (center-to-edge drag) and polygonal (click vertices, finish explicitly) ROIs, attached to individual Z planes.
- Per-ROI Pearson, Spearman, Manders overlap, raw/thresholded Manders fractions, channel intensities and standardized multichannel regression.
- Zero, manual per-channel and Costes-style automatic thresholds; explicit unavailable cases.
- Locally saved ROI analyses, restored with their imported image and exported with source identity and settings.
- Corrected FWHM coordinate conversion, tested against a Gaussian reference at multiple sampling intervals.
- A calibrated, downsampled 3D volume preview with all-channel compositing or individual channel selection, an oblique starting view, display opacity/cutoff controls and labeled Z stretching. Display downsampling does not alter source pixels.
- Local, persistent import records with UUID identity and SHA-256 source digest.
- An Electron launcher, local-session authentication, and initial build/CI configuration.

## Not implemented yet

Biological validation of colocalization, spatial null models, and calibrated significance; volumetric segmentation and organelle measurements; preprocessing and deconvolution; learned super-resolution; Bayesian/MLE workflows; experiment comparisons; the molecular-evidence APIs; the Qwen local agent; reopenable full analysis projects; the marketing website; and full offline installers with models. See [the development plan](docs/DEVELOPMENT_PLAN.md).

There is no claim that the 3D preview or current profile converts conventional images into experimentally acquired super-resolution data. Legacy mock classifications and the PCE discovery score have not been adopted as validated measurements.

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

Choose Circular ROI or Polygonal ROI from the drawing tool, draw one or more regions, select the threshold method, and press **Calculate ROI statistics**. The line profiler remains a separate drawing tool. ROIs use pixel-center coordinates; circular masks are circular in XY pixel coordinates. Measurements use native intensities, independently for each ROI on its recorded Z plane. ROI area uses confirmed X/Y scale. Deleting or adding an ROI or changing analysis settings clears the displayed results until recalculation. The last successfully calculated analysis is restored when reopening a saved import. Unsaved edits do not replace it.

See [ROI measurement definitions](docs/ROI_STATISTICS.md) for formulas and limitations. No probability of molecular binding, calibrated significance or nanoscale resolution is inferred from these descriptive measurements.

## macOS development installation

Version 0.1.2 adds explicit ad-hoc development signing of the Mac app and its bundled analysis executable, plus strict signature checks before producing an installer. This is not Apple Developer ID signing or notarization. Mac development builds may still require an app-specific approval in **System Settings → Privacy & Security → Open Anyway** after attempting to open the app. See [Apple's instructions](https://support.apple.com/en-us/102445). A successful signature check is not a malware or scientific-validation certificate.

If a 0.1.1 installer reports that the app is damaged, replace it with the rebuilt 0.1.2 app rather than disabling Gatekeeper globally. Drag OrganelleScope from the new DMG into Applications and choose Replace. Imported images and analyses are stored separately in the app's user-data directory. The signing hooks clean only FinderInfo/ResourceFork metadata in generated build output and do not remove quarantine from installed apps.

A local packaging run writes installers into `release/` (excluded from Git). CI installers remain available as Actions artifacts until attached to a GitHub Release. Publication-ready Mac distribution requires a Developer ID certificate and notarization configured separately; these credentials are not present in the project.
