# Reproducible XY preprocessing — source 0.1.12

Constant offsets, flat square opening, curved rolling-ball background subtraction and optional Gaussian smoothing run on the CPU using NumPy/SciPy. No extra model, package download or cloud service is needed. **No subtraction and σ = 0 remain the defaults.** The initial radius of 20 pixels is an editable starting entry, not a validated recommendation or an estimate from microscope metadata.

## Exact operations

1. Read the full-resolution unsigned plane and copy to float32.
2. Subtract the selected background estimate:
   - **Constant:** one supplied intensity offset per channel.
   - **Square opening:** erosion followed by dilation with a flat square of width `2*radius_px+1`, reflected boundaries.
   - **Rolling ball:** a curved lower-envelope estimate. For integer XY radius `r` and positive native-intensity height `h`, define `K(dx,dy) = h*sqrt(1-(dx²+dy²)/r²)` inside the disk `dx²+dy² <= r²`. Background at `p` is the minimum of `I(p+q)+h-K(q)` over in-image offsets `q`. This is evaluated by SciPy nonflat grey erosion with structure `K-h`; positive-infinity padding excludes out-of-image samples. Height defaults to radius when absent from the saved recipe. Equal numerical height/radius gives a sphere; other heights give an ellipsoid. No intensity normalization, quantization, downsampling or approximate ball is used. This implements the generalized rolling-ball definition, not a claim of bitwise equivalence with Fiji's implementation/options.
3. Clip negative values to zero, explicitly changing sums and fractions.
4. Optionally smooth with XY Gaussian σ, reflected boundaries, truncation at four standard deviations. σ = 0 disables smoothing.

XY planes and channels are independent: no Z filtering or channel mixing. All analysis uses native spatial sampling, with float32 corrected intensities. At unequal X/Y spacing a circular pixel footprint spans unequal physical distances. Filtering does not establish super-resolution information.

## Choosing settings

Rolling ball assumes bright structures on a darker background. Spatial radius should accommodate the structures you want to retain; height controls how the curved kernel fits the native intensity landscape. A radius suitable for an 8-bit export does not establish a suitable height for a 16-bit acquisition. Both are recorded, and must be assessed against raw data and known controls. Large structures may be removed as background. Noise can distort the background estimate; smoothing also alters spatial correlations, widths and overlap. No universal scientifically validated setting is inferred from metadata.

Rolling-ball radius is limited to 1–100 XY pixels as a computational guard; square-opening radius remains 1–512. Full-resolution rolling-ball work scales with plane area and kernel area, then with channel and Z count. A local engineering timing on the M3 host, 2048 × 2048 uint16 plane, radius 20, default height, σ = 0, took **3.707 seconds** (single run, synthetic sparse bright square on constant background). This is not a general performance guarantee; complete stacks and larger radii take longer.

## Display, measurements and saved recipes

The explorer, drawing surface and 3D renderer display raw images. The preparation comparison uses the same raw-derived channel display ceiling on both sides, without independent brightening. Display clipping/thumbnailing never enters measurements. Apply the recipe, then explicitly select processed intensities for line profiles, ROI statistics or cuboid measurements; raw remains the default.

Filters run on full XY planes before cropping an ROI or cuboid, avoiding artificial ROI-specific boundaries. Only corrected values **inside** the selected ROI/cuboid enter its summary, though their background estimates can depend on outside-XY neighbors. Cuboids use only their selected Z slices. Costes-style automatic thresholding is rejected for corrected floating intensities until separately validated; use zero/manual thresholds.

Algorithm `xy-processing-2` records all settings, NumPy/SciPy versions, float32 arithmetic, operation order, boundaries, kernel definition and effective height, Gaussian truncation, and canonical recipe SHA-256. Saved reports retain source SHA-256 and exact request. Original TIFFs are never rewritten. Older projects without `rolling_height` remain valid; they retain their stored reports until explicitly recalculated. Recipe hashes change with the new algorithm version, including for existing methods.

## Verification and limits

Tests compare rolling-ball results with an independent scalar spherical-surface calculation at image edges and in 8/16-bit ranges; check analytic impulse curvature, constant backgrounds, unchanged source bytes, finite nonnegative float32 output, invalid settings, authenticated plane/preview/recipe APIs, recipe hash changes, and full-plane-then-crop cuboid sums. Existing offset/opening/Gaussian tests remain. These establish numerical behavior, not biological or publication validation. Noise2Void, deconvolution and learned reconstruction remain future work.

References: [SciPy nonflat erosion and its definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.grey_erosion.html), [SciPy grey opening](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.grey_opening.html), [scikit-image rolling-ball definition and intensity-scale examples](https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_rolling_ball.html), [ImageJ radius guidance](https://imagej.net/plugins/rolling-ball-background-subtraction).
