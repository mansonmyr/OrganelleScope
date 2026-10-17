# Release readiness — 0.2.4 research source

## What is ready for evaluation

- Native-unit TIFF import, manual ROI/profile and cuboid measurements, processing/QC, snapshots, inspectable threshold masks and experimental inference are implemented with automated numerical checks.
- Portable project ZIP includes source TIFF, settings, reports and referenced restoration outputs. Imports validate source metadata/hashes, reject unexpected ZIP paths/duplicates/oversized contents, allocate new IDs and preserve existing data. Historical artifacts remain read-only archive data. Archive export represents the **saved** revision, not unsaved controls.
- A separate latest-workspace recovery copy is written after three idle seconds when an image is open. It does not overwrite manually saved projects. Restore is explicit; it is not a multi-revision backup and a newer session can replace this one recovery slot.
- GitHub Actions builds unsigned Windows x64 and macOS ARM64 development installers, with checksums and a frozen-service smoke test. No image-restoration runtime is installed or packaged.

## Build

Install `backend[test]` plus PyInstaller and build normally. There is no restoration extra or denoising/deconvolution installer variant. Builds explicitly exclude CAREamics, PyTorch and Lightning. Optional full-offline Gemma packaging remains separate and unqualified; its 6.98 GB weights are not included in the compact development installer.

## Remaining gates

| Gate | Status / evidence needed |
|---|---|
| Coloc_2 numeric equivalence | 36 aligned fixtures including manual-threshold boundaries; unaligned differences retained. Automatic threshold-search/randomization/JaCoP parity remains outstanding |
| Image restoration | Noise2Void and Richardson–Lucy removed at user request; historical results preserved |
| Mask/object biology | Numerical geometry and containment tests pass; representative organelle/control validation deferred by the user because the images are unavailable |
| Experiment inference | Analytic and reproducibility checks pass; realistic design/coverage and prior sensitivity require review |
| Browser visual/interaction QA | XY wheel zoom and drag panning verified in the browser; source SVG coordinates unchanged. New tabs and persistent preview checked. Native desktop interaction qualification remains |
| Native Windows install | GitHub build/smoke can run; physical/native x64 human test remains required |
| Large workload/memory | Explicit operational budgets; 2048² × four-channel real-stack stress data still needed |
| Signed public macOS release | Developer ID/notarization credentials unavailable; development ad-hoc signing is not Apple notarization |
| Offline LLM installer | Packaging options implemented; full installed/offline/model inference qualification pending |
| Application licensing | User added GNU GPLv3 LICENSE; predecessor noncommercial notices remain retained and component redistribution terms still require reconciliation |
| Marketing/download website | Public launch awaits a verified downloadable release and accurate validation statements |

No repository deletion, overwrite of the installed application, new installer publication or claim of publication certification occurs automatically with this source milestone. Keep exact release/version/checksum and validation status visible when distributing research builds.

Biological validation was deferred on 17 October 2026. Four local samples were subsequently supplied and technically tested; channel-marker assignment, export history and independent experimental units remain unconfirmed, so biological validation is still incomplete.

## Local evaluation build

The local 0.2.4 macOS ARM64 development installer passed read-only disk-image integrity, app/backend development-signature checks, packaged frontend identity and a synthetic API smoke test from the mounted installer. It excludes image-restoration runtimes and the optional multi-gigabyte assistant weights. Signing remains ad-hoc, not notarized. Exact results/checksum are recorded in BUILD_VERIFICATION_0.2.4.json; BUILD_VERIFICATION.json retains the historical 0.2.1 record. Native Windows installation and biological validation remain incomplete.


## Source 0.2.4 follow-up

Editable channel labels, selected-plane acquisition checks and native-range main previews are implemented. The local assistant receives report-aware context and application-generated interpretation notes; synthetic real-model results retain operational failures and qualitative limitations. See INTERPRETATION_AND_QC_0.2.4.md and SOURCE_VERIFICATION_0.2.4.json. No passing software check certifies biological conclusions. Detailed local sample records remain outside the public release.
