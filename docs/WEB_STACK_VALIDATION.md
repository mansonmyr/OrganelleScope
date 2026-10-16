# Z-stack viewing verification — 16 October 2026

This is functional visualization verification, not biological validation or super-resolution benchmarking.

## Cause and changes

A Fiji-saved organ-of-Corti sample used the ASCII literal `\u00B5m` for its ImageJ unit. The importer recognized literal µm and um, but not this escaped form. Valid X/Y/Z calibration was therefore unavailable and the physical volume endpoint correctly refused an uncalibrated rendering. Unit normalization now recognizes the escaped micro sign and Greek mu; import schema 2 refreshes saved imports while retaining explicit user overrides.

The supplied file has 548 × 249 pixels, 15 Z slices, four channels, uint16 values and 0.31500011655 µm spacing on all axes. It is a shallow slab. The center-to-center span of the first and last of its 15 slices is (15−1) × 0.315 ≈ 4.41 µm; a 15-voxel extent convention yields 4.725 µm as in Fiji's depth summary. Those are distinct extent conventions. Smaller spacing is sampling, not proof of optical resolution.

The 3D viewer now starts obliquely, composites up to four independent scalar components in one ray-cast volume, and offers all-channel or individual-channel selection. Transfer functions remain separate for each component. Opacity and background cutoff operate only on rendering. Optional Z stretch is explicitly marked as exaggerated and changes the actor display scale, not source calibration, pixels or measurements. Physical scale remains the default when available; otherwise the endpoint offers an explicit voxel-unit preview without inventing µm values. Unconfirmed scientific axes still block rendering.

## Public samples

Downloaded from the [ImageJ sample collection](https://wsr.imagej.net/ij/images/). The TIFF files are saved locally under `local-samples/ImageJ/`, excluded from Git, with source URLs and SHA-256 hashes in `sources.json`. User-supplied TIFFs remain local.

| Sample | Native layout | Calibration from metadata | Result |
|---|---|---|---|
| [Confocal brain stack](https://wsr.imagej.net/ij/images/confocal-stack.zip) | 370 × 370 × 36 Z; RGB uint8 | X/Y ≈ 0.197904 µm; Z = 0.5 µm | Source planes and all three component volumes returned; combined rendering observed |
| [Flybrain](https://wsr.imagej.net/ij/images/flybrain.zip) | 256 × 256 × 57 Z; RGB uint8 | X/Y ≈ 2.675521 µm; Z ≈ 3.947368 µm | Source planes and all three component volumes returned; combined rendering observed |
| Supplied Fiji organ-of-Corti crop | 548 × 249 × 15 Z; four channels uint16 | X/Y/Z ≈ 0.315 µm | Automatic escaped-unit extraction; all four volumes and combined rendering observed |

The two public RGB files store interleaved colour samples (ZYXS). For this rendering test, their explicit sample axis was confirmed as C (ZYXC). They are display RGB components, not a guarantee of original independent detector channels; do not use them as biological colocalization ground truth. The flybrain metadata also says it was smoothed and resampled before distribution. Sample attribution is retained in each TIFF's ImageJ Info field (confocal brain: Tony Collins; flybrain: Benjamin Schmid/Heisenberg lab; organ of Corti: Glen MacDonald).

## Checks

- 32 backend tests pass, including escaped and literal micro-unit variants, explicit uncalibrated voxel rendering, downsampled geometry, preserved unknown source scale, and rejection of unknown unit modes.
- 20 interface tests pass, including four-channel voxel interleaving and the calibration popup.
- Frontend type checking and production build pass.
- Browser verification observes the popup and all-channel 3D volumes; a four→one→four channel switch renders without recorded browser errors. Display Z stretch shows its warning.

The display is bounded at roughly 128 × 128 × 64 per channel. Rendering quality is therefore a preview, not a full-resolution 3D analysis result. Larger datasets and native Windows GPU testing remain separate validation work.
