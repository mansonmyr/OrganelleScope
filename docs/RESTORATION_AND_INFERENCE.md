# Restoration, masks, snapshots and experiment inference

Source milestone 0.2.0, 17 October 2026. These are implemented research workflows, not certification for publication or a claim to recover molecular resolution. Keep raw measurements as a baseline and review processing effects before interpreting a biological difference.

## Preview capture and processing verification

The shared preview offers **Capture PNG**, optional visible XY ROI overlays and a separate JSON details export. XY capture uses the displayed preview's natural dimensions; volume capture uses the current rendered camera. It records source SHA-256, calibration, Z/channel selection, display-only scope and volume settings. Neither PNG is a replacement for native quantitative TIFF pixels. The volume is downsampled, and exaggerated Z stretch remains display-only. Threshold surfaces, when present, are included in the 3D capture.

Image preparation offers matched-contrast raw/processed, estimated background and absolute residual views. **Measure processing changes** computes full-plane native-unit means/sums, net intensity change, changed-pixel count, residual RMSE and adjacent residual correlation. A small residual or visually smooth image is not validation; persistent structures in residuals can indicate signal removal. Negative net removal means processing increased summed intensity. Raw explorer and volume intensities remain the original data; processed measurements are explicitly selected.

## Noise2Void

Install the optional `backend[restoration]` runtime (CAREamics 0.3.4, PyTorch/torchvision pinned in the backend manifest), or build the restoration installer edition. A compact installer does not include this runtime and reports its absence explicitly.

1. Import matching raw acquisitions, including separate training and validation images. Source checksums must differ; use held-out acquisitions for evaluation, not only random patches from the same image.
2. Select training images, separate validation image, epochs, steps, patch size and seed. The implementation is a 2D, independent-channel UNet, trained on native-unit XY patches sampled from Z stacks. It does not learn cross-channel or axial correlations. Recorded training mean/std normalization is inverted on prediction.
3. Export/import the small tensor-only ZIP if needed. No uploaded Python/pickle checkpoint is executed. Hashes, numeric tensors, channel count, bit depth and normalization are checked; strict architecture compatibility is checked before inference. A trusted temporary Lightning checkpoint is generated locally from these verified tensors because CAREamics requires that format internally.
4. Review channel/acquisition/noise compatibility before applying the model. Prediction uses overlapping tiles and stores verified float32 results bound to exact source-plane contents and Z indices. Activate a completed result to use it in processing comparisons and measurements. Background correction, clipping negatives to zero and optional smoothing follow restoration.

Jobs expose progress, cancellation and restart-interruption status. Partial results and duplicate temporary training checkpoints are removed; completed models, results and source images are preserved. Disk/patch/volume budgets are enforced. A validation loss is a diagnostic rather than proof of biological fidelity.

**Measured synthetic result:** three untouched Poisson-noise test images had raw MSE 60.50–73.12, N2V MSE 22.21–23.38 and Gaussian σ=1 MSE 7.30–9.71. N2V summed-intensity bias was −1.04% to −2.16%. Thus N2V helped relative to raw noise but did **not** outperform the Gaussian reference on this simulation. No universal model is bundled from these synthetic images. See [exact results](N2V_SYNTHETIC_BENCHMARK.json) and the reproducible script in `scripts/validation/benchmark_n2v.py`.

Noise2Void assumes predictable signal with noise that is sufficiently independent between pixels. Structured/correlated detector noise, different acquisition settings and faint/small structures require separate validation. No claim of super-resolution follows from denoising. Primary references: [original N2V paper](https://openaccess.thecvf.com/content_CVPR_2019/html/Krull_Noise2Void_-_Learning_Denoising_From_Single_Noisy_Images_CVPR_2019_paper.html), [CAREamics configuration](https://careamics.github.io/latest/reference/careamics/config/factories/n2v_factory/), [checkpoint/prediction guidance](https://careamics.github.io/latest/content/guides/current/careamist_predicting/).

## PSF-based deconvolution

Richardson–Lucy uses full native-intensity XYZ volumes per channel, a nonnegative unit-mass spatially invariant PSF and a Poisson observation model. Reflect-padding by the PSF radius precedes iteration; results are cropped back to source shape, without unit-range clipping or 8-bit normalization. The iteration count is explicit and can amplify noise.

Select a single-channel measured PSF with matching dimensionality, odd axes up to 129 voxels and spacing matching within 1%, or supply explicit Gaussian XY/Z standard deviations in µm. Gaussian widths are model assumptions, not measured resolution. No silent PSF resampling occurs. The selected PSF is used for every channel; wavelength-dependent PSFs need acquisition-specific handling. The current input budget is 512 MiB per channel with a conservative 2 GiB estimated padded working-memory limit; large XYZ stacks or PSFs can be rejected explicitly. Additive detector background and non-Poisson noise can violate the likelihood assumptions.

A numerical test compares the implementation to [scikit-image Richardson–Lucy](https://scikit-image.org/docs/stable/api/skimage.restoration.html#skimage.restoration.richardson_lucy) with the same padding and clipping convention. This establishes implementation agreement under those settings, not resolution recovery in experimental images.

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

## Packaging findings

Packaged tests exposed missing bioimageio static data and recursive distribution metadata. The restoration build now includes these resources explicitly. CAREamics 0.3.4 selects its masking random-generator device separately from Lightning's accelerator; OrganelleScope explicitly pins that generator to CPU to match the declared CPU training baseline on Macs with available Metal acceleration. No upstream algorithm is replaced.

## Hierarchical resampling audit

[Repeated-sampling audit](HIERARCHICAL_SYNTHETIC_BENCHMARK.json): with four cells per experiment and Gaussian between/within-experiment variation, 100 simulations per case gave nominal 95% percentile-bootstrap coverage of 89% (three experiments per condition) and 92% (eight). At three independent experiments per condition the exact two-sided permutation test cannot reach p≤0.05 (20 assignments; minimum p=0.1); adding pixels or ROIs does not change that. At eight experiments the observed null rejection rate was 7/100, with substantial Monte Carlo uncertainty. These results limit claims; the interface labels intervals nominal and reports permutation resolution rather than claiming calibrated publication-ready inference.

The rebuilt frozen macOS ARM64 service passed real tiny N2V training, verified tensor reload, tiled inference and processing-result delivery with Metal available but CPU training selected. [Packaged test record](PACKAGED_RUNTIME_BENCHMARK.json). This verifies dependency packaging and execution, not model quality.

[Structured-noise/measurement audit](RESTORATION_BIAS_BENCHMARK.json) showed summed-intensity bias of −5.84% and −8.52% for two additional synthetic conditions, despite lower MSE than raw. The true Pearson coefficient was 0.8348; restored values were approximately 0.842. Better appearance or MSE therefore does not establish unbiased channel association.
