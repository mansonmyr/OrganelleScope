# Manual ROI batch analysis and Excel export

Source milestone 0.1.10. This is an engineering-tested development feature; it does not supply biological validation or experiment-level statistics.

## Workflow

1. Open **Batch analysis** and upload multiple TIFF/OME-TIFF files, up to 50 per batch. Import failures are reported individually. Each import retains its own source identity; no saved project is required.
2. Select an image from the queue. Confirm its axes, channel count, series and physical calibration. The expandable calibration controls apply to this image only. An image needs at least two channels for the current analysis.
3. Choose a Z plane. For a calibrated circle, select **Place circle by diameter**, enter a diameter in µm, and click its center. The default is 2 µm **diameter**, not radius. Alternatively, turn off diameter placement and drag a pixel circle, or choose polygon and finish its vertices explicitly.
4. Adjust individual circle diameters with **Apply diameter**, or delete and redraw a region to change its position/boundary. Each ROI belongs to its recorded XY plane; there is no Z propagation, projection or 3D ROI inference. A physically circular region can appear elliptical in pixel coordinates when X/Y spacing differs. All masks include pixel centers, so very small regions may contain too few pixels to analyze.
5. Set the per-image threshold mode, regression target and optional background/smoothing recipe. The viewer shows the raw image; the preprocessing comparison identifies processed values. Automatic Costes-style thresholds are supported only for raw intensities. Optional experiment/cell/condition labels are preserved without treating ROIs or pixels as biological replicates.
6. Check **I reviewed the ROIs, calibration, channel mapping and settings for this image**. Repeat for every image. Changing an ROI or settings clears its review. Nothing draws ROIs automatically; Gemma is not used to locate structures or execute batch measurements.
7. **Save batch** retains the editable queue independently from one-image projects. **Analyze reviewed batch** saves first, then freezes that revision into a separate run. If another workspace changed calibration since the last save, affected images must be reviewed again. Reopening another saved batch or starting a new one asks before discarding unsaved changes.
8. Watch image statuses and inspect each result. Cancellation is cooperative between source-hash chunks, planes, channels and ROIs; a running numerical operation can take time to return. Completed results survive cancellation. A failed source/hash/ROI is reported and other images continue. App restart marks unfinished runs interrupted; it never silently resumes analysis.
9. Export the **Excel workbook** and **full JSON**. Select an earlier run to export it again. Later edits to the queue do not change earlier runs.

## What Excel contains

Seven sheets: Read me, Images, Settings, ROI geometry, Colocalization, Intensities and Regression. These include source SHA-256, image-level status/failure, optional experiment labels, channel names, calibration provenance, processing recipe, threshold choices, ROI vertices and diameter, engine version and computed values/warnings. Z planes and target channels are one-based in Excel; the original JSON uses zero-based indices.

Blank numeric cells mean unavailable/undefined, never zero. Measurements are stored as numeric cells; user text is stored literally, including strings beginning with `=`. The workbook contains no formulas or external links. A portable application exporter writes OOXML without Excel installation or a cloud API. Workbook headers use the application's teal and #FFECD1 palette. JSON retains full native metadata and nested calculation provenance; preserve it with the workbook for reproducibility.

Excel exports are limited to two million cells, the Excel row limit and its 32,767-character cell limit. An explicit error replaces any silent truncation; split the batch or use JSON if needed. Batch import has the existing 8 GiB per-file cap. Source decoding and measurement run sequentially; this is not a claim of validated performance for arbitrarily large images or a tested 30-image real-data benchmark.

## Statistical scope and preservation

The same deterministic analysis service calculates interactive and batch results. There is no averaging of p-values, unvalidated significance test, interaction probability, automatic hypothesis or biological replicate pooling. The Gaussian likelihood-ratio statistic remains descriptive under its documented covariance model. See [ROI definitions](ROI_STATISTICS.md) and [validation status](VALIDATION.md).

Sessions and frozen runs live under `batch-data/` inside the application's image-data directory. They are research records, not disposable cache. Imported images, ROIs and results are not deleted by removing a queue entry. Sessions are manual-save, local records with revision conflict checks; portable migration and autosave remain pending.

## Development verification — 17 October 2026

- Analytic anisotropic circle-mask checks, missing-calibration rejection and clipping/legacy-circle checks.
- Independent per-image ROIs and recipes; batch output equals interactive output, including a processed image. Review gating, revision conflicts, source hash mismatch, per-image failures, immutable earlier runs, cooperative cancellation and restart interruption checks.
- Interface checks cover manual placement, resize/review invalidation, independent image queues and keeping a batch draft while opening another single-image project. A live two-image synthetic OME-TIFF queue (2 channels, 3 Z planes; X 0.1/Y 0.2 µm) completed with different circle diameters and reopened from disk.
- Live authenticated Excel export opened with an independent OpenPyXL reader; seven sheet names, numeric values, ROI diameters and styles were checked against the saved engine result. Formula-like user text and blank undefined measurements have separate OOXML regression checks. The in-app testing browser lost its tab during a browser download-event check; the export endpoint and downloaded workbook were verified separately. Native desktop Save/Download behavior and Windows Excel/Apple Numbers rendering remain to be checked.

The full source test run at this milestone passed 98 backend tests and 37 frontend tests, plus the frontend production build. These are engineering checks, not publication validation or proof of a large real-data workload.
