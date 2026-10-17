# Cuboid arithmetic verification and empty RGB components

Source milestone 0.1.11; checked 17 October 2026. This is a source-data and arithmetic check, not biological or publication validation.

The reported UI example used `confocal-stack.tif`, an ImageJ-format, 8-bit TIFF with 36 × 370 × 370 × 3 stored values. Its TIFF photometric interpretation is **RGB**, and its native series axes are `ZYXS`. The previously confirmed application interpretation was `ZYXC`; these are stored color components, which must not automatically be identified with independent original microscope channels.

The selected inclusive cuboid was X = 0–63, Y = 0–63, Z = 0–35: **147,456 voxels**. This is the upper-left XY region through the stack, irrespective of where a crosshair was displayed. The old UI moved only the crosshair on click; cuboid bounds were editable numerically. The updated UI supports cuboid dragging, click placement, keyboard movement and centering. A dashed box indicates that a linked section is outside the selected cuboid and shows only its projected bounds.

## Independent read of this local sample

A direct `tifffile.TiffFile(...).series[0].asarray()` read was compared with every application-decoded channel plane. The selected source values matched exactly. NumPy's independent correlation calculation and SciPy's rank correlation were then applied to the direct TIFF crop.

| Quantity | Direct reference | UI, rounded |
| --- | ---: | ---: |
| Channel 1 sum | 245166 | 245,166 |
| Channel 1 mean | 1.6626383463541667 | 1.6626 |
| Channel 1 population SD | 3.7268196386449435 | 3.7268 |
| Channel 1 nonzero voxels | 97059 | 97,059 |
| Channel 2 sum | 211175 | 211,175 |
| Channel 2 mean | 1.4321221245659723 | 1.4321 |
| Channel 2 population SD | 1.515724801501801 | 1.5157 |
| Channel 2 nonzero voxels | 114190 | 114,190 |
| Channel 1 / 2 Pearson | 0.11369332721656863 | 0.1137 |
| Channel 1 / 2 Spearman | 0.18035304333748872 | 0.1804 |
| Channel 3 sum, SD and nonzero count | 0 | 0 |

Channel 3 was also zero across the **entire stored stack**, not just this cuboid. Its absence of recorded variation makes Pearson and Spearman mathematically undefined. For A = Channel 1 and B = Channel 3, M1 is a defined zero because no A intensity lies where B > 0; M2 is unavailable because its B intensity denominator is zero. This does not prove that a protein is biologically absent. An unused blue component of an RGB export is one possible explanation; consult the original acquisition and use independent microscope channel data for biological analysis when available.

## Automated regression coverage

A separate small, three-component RGB stack is generated during tests. A direct TIFF array crop is compared with the API cuboid's inclusive voxel count, channel sums/SDs, Pearson, Spearman and both directional Manders fractions. Its empty component tests defined-zero versus undefined results and the metric-specific explanations. Movement tests preserve the cuboid size, clamp at source edges and confirm that the bounds sent for measurement match those shown after dragging or keyboard movement.

ROI and cuboid values remain deterministic application calculations, independent of Gemma. A numerically correct coefficient does not establish binding, organelle segmentation, optical resolution or an appropriate biological experimental design. See [ROI statistics](ROI_STATISTICS.md) and [validation limits](VALIDATION.md).

## XYZ containment and resizing — 0.1.12

Width X and Height Y are integer voxel counts; Depth Z is the number of consecutive slices. Changing size preserves the geometric center where possible (half-voxel ties round toward the smaller index), then shifts the whole cuboid inside image edges. Exact start/end indices remain editable. Physical extents are count × spacing, rather than the distance between the centers of the first and last voxels. Result displays clear when bounds change.

An API regression uses distinct intensities on Z = 1 and Z = 2 with X = 3–5 and Y = 2–3. The selected 12 voxels sum to 1830 in channel A. Replacing **all outside XYZ voxels** with 65000 leaves raw channel and pair metrics unchanged. Increasing one selected voxel by 7 changes the sum to 1837. Selecting only Z = 2 gives 6 voxels summing to 1215. This tests both inclusive Z endpoints, rather than a projection or all-stack summary. UI tests resize XYZ and inspect the exact request bounds.

For processed measurements the selected source Z planes are each corrected in full XY **before** cropping. Statistics still include only the cropped voxels, but background/smoothing estimates can depend on neighboring pixels outside XY bounds. No outside Z slice is used. A rolling-ball cuboid regression compares sums against this full-plane-then-crop definition. This is intentionally different from filtering only an isolated crop, which would introduce ROI-edge artifacts.
