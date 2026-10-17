# Release readiness — 0.2.0 research source

## What is ready for evaluation

- Native-unit TIFF import, manual ROI/profile and cuboid measurements, processing/QC, snapshots, inspectable threshold masks and experimental inference are implemented with automated numerical checks.
- Portable project ZIP includes source TIFF, settings, reports and referenced restoration outputs. Imports validate source metadata/hashes, reject unexpected ZIP paths/duplicates/oversized contents, allocate new IDs and preserve existing data. Training model weights are separate exports. Archive export represents the **saved** revision, not unsaved controls.
- A separate latest-workspace recovery copy is written after three idle seconds when an image is open. It does not overwrite manually saved projects. Restore is explicit; it is not a multi-revision backup and a newer session can replace this one recovery slot.
- GitHub Actions builds unsigned Windows x64 and macOS ARM64 development installers, with checksums and a frozen-service smoke test. The CPU restoration runtime is selected by default; uncheck the workflow input for the compact edition. Development tags include restoration.

## Build editions

Compact: install `backend[test]` plus PyInstaller; build normally. N2V reports runtime unavailable, while background filters, deconvolution and segmentation remain available.

Restoration: install `backend[test,restoration]` plus PyInstaller; set `ORGANELLESCOPE_INCLUDE_RESTORATION=1` for backend packaging. This adds CAREamics/PyTorch and increases size materially. Native build-time license collection is included. Tests train/reload/apply a tiny independent synthetic model; this checks plumbing, not useful model quality.

Full offline assistant: use the existing pinned setup script for the platform's official llama.cpp runtime and selected Gemma model, then set `ORGANELLESCOPE_INCLUDE_ASSISTANT=1` for `scripts/package-desktop.mjs`. The model SHA-256 is checked before copying. The desktop launcher points the Python service to the bundled model/runtime. This option is configured but a complete multi-platform offline installer is **not yet qualified**. Gemma weights alone are 6.98 GB decimal; a small installer containing this model is impossible. GitHub single-asset limits and distribution strategy must be addressed before publishing a full offline edition. Do not silently upload multi-gigabyte assets or bundle retired models.

## Remaining gates

| Gate | Status / evidence needed |
|---|---|
| Coloc_2 numeric equivalence | Passed for 12 fixtures and three metric families only; threshold/randomization/JaCoP comparisons outstanding |
| N2V experimental quality | Synthetic test improves raw MSE but loses to Gaussian reference; real acquisition/structure/noise validation pending |
| Mask/object biology | Numerical geometry and containment tests pass; representative organelle/control validation deferred by the user because the images are unavailable |
| Experiment inference | Analytic and reproducibility checks pass; realistic design/coverage and prior sensitivity require review |
| Browser visual/interaction QA | Blocked by browser access policy in this run; do not treat component tests as visual verification |
| Native Windows install | GitHub build/smoke can run; physical/native x64 human test remains required |
| Large workload/memory | Explicit operational budgets; 2048² × four-channel real-stack stress data still needed |
| Signed public macOS release | Developer ID/notarization credentials unavailable; development ad-hoc signing is not Apple notarization |
| Offline LLM/ML installer | Packaging options implemented; full installed/offline/model inference qualification pending |
| Application licensing | User has not selected a new application license; predecessor noncommercial terms retained |
| Marketing/download website | Public launch awaits a verified downloadable release and accurate validation statements |

No repository deletion, overwrite of the installed application, new installer publication or claim of publication certification occurs automatically with this source milestone. Keep exact release/version/checksum and validation status visible when distributing research builds.

Biological validation was explicitly deferred by the user on 17 October 2026 because the control images could not be located. This does not block further development; it remains a documented scientific limitation.

## Local evaluation build

A macOS ARM64 0.2.0 development DMG is built locally in `release/OrganelleScope-0.2.0-arm64.dmg` (approximately 303 MiB), including the CAREamics CPU runtime. It uses ad-hoc development signing and is not notarized. It does not include the 6.98 GB Gemma weights or standalone llama.cpp assets; full-offline assistant distribution remains a separate qualification gate. The installed older application is not overwritten. Local automated totals: 132 backend tests and 59 interface tests; UI production build passed. No live visual QA or native Windows installation result is claimed.
