# Reproducible XY preprocessing

The first preprocessing milestone supports constant background offsets per channel, local background subtraction with a flat square grayscale opening, and optional Gaussian smoothing. These deterministic filters run on the CPU using existing SciPy dependencies. No model weights or cloud service are required.

## Exact operations

1. Read the full-resolution unsigned source plane and copy to float32.
2. Subtract either the specified channel offset or a grayscale opening of the plane. The opening has a flat square footprint of width `2*radius_px+1`, and reflected boundaries. It is not a rolling-ball implementation.
3. Clip negative values to zero. This convention changes intensity sums and fractions; it is recorded explicitly.
4. Optionally smooth with a Gaussian of `sigma_px` in each XY axis, reflected boundaries and kernel truncation at four standard deviations. Zero sigma disables smoothing.

Each channel and Z plane is independent. No Z filtering, channel mixing, resampling or intensity normalization enters quantitative measurements. XY pixel units can represent different physical widths when X and Y calibration differ. No super-resolution information is established by filtering.

Choose a window wider than the structures to preserve. A local opening can remove broad biological signal along with background. Gaussian smoothing changes spatial correlations, peak widths and apparent overlap. Neither setting is inferred automatically from microscope metadata. Compare results on raw data and known controls, and report the chosen settings.

## Display and measurement

The source explorer, drawing surface and 3D renderer retain raw-image displays. The preparation panel shows raw on the left and processed on the right using the *same* per-channel raw-derived display ceiling (99.5th percentile of a stride-four sample, with maximum/one fallback). Thus the processed view is not independently brightened. Display clipping and thumbnailing do not enter measurements.

Raw is the default measurement source. Users must explicitly select processed measurements after applying a nonidentity recipe. This choice applies to line profiles and ROI statistics. The latter use the full plane processing before masking an ROI, avoiding ROI-specific filter boundaries. Line traces retain floating values. Existing approximate three-pixel smoothing used solely for FWHM extraction is separately labelled in the chart.

Costes-style automatic thresholding remains available for raw integer images. It is rejected for processed measurements until a continuous-intensity version is separately validated; zero or manual thresholds are available. Filtering is not evidence of molecular binding, and current statistics still lack independent biological publication validation.

## Provenance

The JSON inspection export records the source file SHA-256, import/calibration settings, applied recipe, selected measurement source, ROIs and available measurements. The recipe records processing algorithm version, settings, NumPy/SciPy versions, arithmetic type, operation order, boundary handling, footprint and Gaussian truncation, plus a SHA-256 of this canonical recipe. Saved ROI analyses contain their own measurement recipe, source SHA-256 and request. The original imported TIFF is never rewritten. A recipe is persisted through an analysis/export; there is no separate saved project session yet.

## Numerical verification

Tests cover exact fractional offset subtraction near the 16-bit range, clipping without unsigned wraparound, preservation of source bytes, recovery of a known isolated signal above a constant background, Gaussian symmetry/constant preservation/impulse flux, invalid inputs and authentication, float32 delivery, processed ROI sums, raw/processed isolation, saved recipe round trips and rejection of unsupported automatic thresholds. These establish engineering behavior, not biological validation. Model-based Noise2Void denoising, deconvolution and spatial significance inference remain separate future milestones.

Primary implementation references: [SciPy grayscale opening](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.grey_opening.html) and [SciPy Gaussian filtering](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html).
