# OrganelleScope

A desktop microscopy workbench in development, bringing together the Probabilistic Colocalization Estimator and Quick IF Line Profiler.

**Current milestone: metadata, calibrated viewing, and source line profiles. This is a development build, not a validated scientific release.**

## Available now

- TIFF, OME-TIFF and ImageJ TIFF inspection with source bit depth, channel names, shape, axis order and calibration provenance.
- Explicit correction of ambiguous axes; no automatic disposal of Z planes or time points.
- Conflicting physical-scale metadata blocks physical interpretation until corrected.
- Page-wise viewing of supported uint8/uint16 layouts, up to four channels.
- Native-intensity line profiles on a selected XY plane, calibrated for unequal X/Y spacing.
- Corrected FWHM coordinate conversion, tested against a Gaussian reference at multiple sampling intervals.
- A single-channel, calibrated, downsampled 3D volume preview. Display downsampling does not alter source pixels.
- Local, persistent import records with UUID identity and SHA-256 source digest.
- An Electron launcher, local-session authentication, and initial build/CI configuration.

## Not implemented yet

Validated colocalization and spatial null models; volumetric segmentation and organelle measurements; preprocessing and deconvolution; learned super-resolution; Bayesian/MLE workflows; experiment comparisons; the molecular-evidence APIs; the Qwen local agent; reopenable full analysis projects; the marketing website; and full offline installers with models. See [the development plan](docs/DEVELOPMENT_PLAN.md).

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

`npm run package` builds the UI and a PyInstaller backend, then packages with Electron Builder. Install PyInstaller in the selected Python environment first. Initial targets are macOS ARM64 and Windows x64; Windows ARM and native GPU support require further evaluation. The manual GitHub packaging workflow generates unsigned development artifacts, not a complete production release. No LLM or restoration weights are bundled at this stage.

## Sources and license status

The original repositories remain independent and have been backed up outside this repository. See [migration notes](docs/MIGRATION.md) and [third-party notices](third_party/NOTICE.md). The original projects use PolyForm Noncommercial 1.0.0. A final license for newly written OrganelleScope code has not been chosen; public availability alone does not grant an additional license.

No experimental TIFFs, credentials, model weights, or local environments belong in this repository.
