# Background processing, masks, snapshots and experiment inference

Source milestone 0.2.1, 17 October 2026. These are implemented research workflows, not certification for publication or a claim to recover molecular resolution. Keep raw measurements as a baseline and review processing effects before interpreting a biological difference.

## Preview capture and processing verification

The shared preview offers **Capture PNG**, optional visible XY ROI overlays and a separate JSON details export. XY capture uses the displayed preview's natural dimensions; volume capture uses the current rendered camera. It records source SHA-256, calibration, Z/channel selection, display-only scope and volume settings. Neither PNG is a replacement for native quantitative TIFF pixels. The volume is downsampled, and exaggerated Z stretch remains display-only. Threshold surfaces, when present, are included in the 3D capture.

Image preparation offers matched-contrast raw/processed, estimated background and absolute residual views. **Measure processing changes** computes full-plane native-unit means/sums, net intensity change, changed-pixel count, residual RMSE and adjacent residual correlation. A small residual or visually smooth image is not validation; persistent structures in residuals can indicate signal removal. Negative net removal means processing increased summed intensity. Raw explorer and volume intensities remain the original data; processed measurements are explicitly selected.

## Inspectable compartment masks and spatial measurements

Move/resize the 3D cuboid, then select a marker channel and Otsu or manual threshold. Six-neighbor connected components and a minimum voxel count define objects. Drawn XY circle/polygon ROIs can add/remove mask pixels only on their recorded Z planes; edits outside the cuboid Z range fail explicitly. Exclude reviewed object IDs and recalculate. An object label such as centrosome, mitochondria, nucleus, microtubule or Golgi is user-provided biological context, not an automated organelle classifier. Touching structures can merge; watershed/learned classifiers are not claimed.

Measurements include voxel count, physical volume when XYZ spacing is known, global centroid, principal RMS extents, all-channel sums/means and cuboid-boundary flags. The shared volume preview can display an orange marching-cubes threshold surface. Meshes are capped at 50,000 vertices/100,000 faces; cut faces are closed for display and are not measured membranes. Export contains cropped uint32 OME label TIFF and full measurement JSON with original cuboid origin/bounds.

Optional reference-channel proximity uses a distance transform with calibrated XYZ spacing. It reports marker-to-reference occupied voxel-center distances and the empirical conditional fraction `P(distance ≤ d | marker foreground)`. This is neither a probability of molecular binding nor a voxel-independent significance test. Registration, PSF and label/linker errors are unmeasured.

Radial enrichment uses spherical shells around the selected foreground centroid (or an API-supplied source-coordinate center). Shells intersect the selected cuboid; counts and sampled volumes are reported without extrapolating cut shells. Enrichment divides shell mean by whole-cuboid mean; empty shells/zero denominators are undefined. Interpret this ratio in the context of background and selected bounds. References: [Otsu](https://scikit-image.org/docs/stable/api/skimage.filters.html#skimage.filters.threshold_otsu), [region and surface measurements](https://scikit-image.org/docs/stable/api/skimage.measure.html), [calibrated distance transform](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.distance_transform_edt.html).

## Experiment comparisons, MLE and Bayesian uncertainty

Use a completed batch with explicit condition, independent experiment and cell IDs. Choose paired experiments only for genuinely matched experimental units. Unmatched paired experiments and overlapping IDs in an independent design are rejected. Undefined/failed selected measurements are not silently dropped. Processing/threshold conventions and restoration models must match across selected images.

The engine averages ROIs within each cell and cells within each experiment, then weights experiments equally. The operational minimum is three experiments per condition; this is a software guard, not a universal adequate sample size. Hierarchical percentile bootstrap resamples experiments and cells; paired resampling preserves experiment pairing (not individual cell pairing). A two-sided experiment-level permutation test uses the chosen design. Benjamini–Hochberg adjustment covers all contrasts **for one metric in this report**, not additional metrics or reports.

The optional Gaussian model exposes the MLE experiment mean and sigma (population denominator n), and a Normal–inverse-Gamma posterior for unknown mean/variance. Priors are visible and recorded. It is offered for intensity means or Fisher-transformed correlations; native bounded fractions/correlations retain descriptive/bootstrap summaries. Fisher z at ±1 is rejected rather than clipped. Beta has squared analysis units. Posterior mean, Student-t credible interval, expected sigma² and variance of mu are distinct quantities. Automatic beta×0.1/×10 sensitivity and experiment means are included; normality checks are descriptive and cannot establish normality with small samples.

**Calibration limitation:** with the illustrative default prior, simulated nominal 95% Bayesian credible intervals covered fixed true means only 83.7–90.5% at n=5 in the two tested scenarios; coverage approached 93.8–94.6% at n=50. These are conditional Bayesian intervals, not guaranteed frequentist 95% confidence intervals. Inspect priors and model assumptions rather than choosing the prior that produces a desired result. See [simulation](INFERENCE_SYNTHETIC_BENCHMARK.json). Hierarchical bootstrap coverage under realistic laboratory designs remains a separate validation gate.

References: [pseudoreplication in cell biology](https://pmc.ncbi.nlm.nih.gov/articles/PMC2817684/), [hierarchical bootstrap](https://pmc.ncbi.nlm.nih.gov/articles/PMC7906290/), [SciPy permutation conventions](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html), [Gaussian conjugate analysis and parameterization](https://www.cs.ubc.ca/~murphyk/Papers/bayesGauss.pdf).

## Direct Fiji benchmark

The installed Fiji Coloc_2 3.1.0 Java classes were called directly on 12 seeded native 8/16-bit fixtures, with full and irregular masks, ties/zeros and positive/negative/independent signals. Pearson, Spearman and zero-threshold Manders agreed with maximum absolute difference 4.44×10⁻¹⁶. [Exact report and jar hash](COLOC2_BENCHMARK.json). Costes automatic threshold search/rounding, randomization, JaCoP, biological controls and performance equivalence are outside this benchmark.


## Removed image-restoration features

Noise2Void training/inference and Richardson–Lucy deconvolution were removed at the user’s request. Gaussian smoothing and background subtraction remain. No CAREamics/PyTorch restoration runtime is installed or packaged. Archived restoration artifacts/reports are preserved for historical export only; new calculations with an old restoration result are rejected. Opening such a project creates a clearly labelled recalculation copy with original calibration/ROIs and supported background/smoothing settings, clears stale reports from that copy, and preserves the original saved project. A historical recovery copy is retained before replacing its recovery slot.

## Preview zoom and separate workspaces

The persistent preview offers XY zoom from 25% to 800% of the fitted image, scrollbars for inspecting enlarged areas and **Fit image**. Source aspect ratio, voxel calibration and ROI coordinates do not change. 3D has explicit camera zoom buttons alongside the existing scroll-wheel zoom. Zoom/camera state stays mounted across workspace tab switches. XY PNG capture continues to export the full preview plane with its ROI overlay; it does not crop to the inspection viewport.

Background correction, ROI measurements and Channel associations have separate tabs beneath the shared preview. ROI measurements contains geometry/intensity summaries; Channel associations contains the existing colocalization/regression results. The Image & ROI tab retains line profiles.

## XY inspection gestures

The XY preview accepts trackpad pinch and wheel zoom, anchored at the pointer, from 25–800% of the fitted view. Pan image enables left-button dragging; Space-drag and middle-button drag pan temporarily. Disable Pan image for ordinary ROI drawing. Fit image resets inspection zoom and scroll position. These controls change only display geometry, never TIFF pixels, ROI coordinates or physical calibration. PNG captures retain the entire XY plane.
