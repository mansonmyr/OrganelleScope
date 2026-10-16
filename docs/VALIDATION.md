# Foundation verification — 16 October 2026

This records engineering checks for the first milestone. It is not a biological validation certificate.

- 27 backend tests pass in an isolated environment. Coverage includes OME/ImageJ scale extraction, generic print-DPI refusal, source identity, persistent-record refresh, axis confirmation, all C/Z planes, compressed/endian variants and bounded calibrated volume geometry.
- 18 frontend tests pass, including the analytical Gaussian FWHM regression across 0.5, 1 and 2 pixel sampling intervals.
- Frontend type checking and production build pass.
- All 15 supplied PCE TIFF examples open through the new importer in their source uint8/uint16 type. These examples were inspected locally and were not uploaded.
- Browser verification on a generated four-channel synthetic 31-plane OME stack confirms channel names, 0.100 × 0.100 × 0.250 µm spacing and an interactive single-channel 3D preview. This small-volume check does not establish performance on 2048×2048 stacks.
- Electron desktop startup and its session-authenticated image-service connection have been observed on the development Mac.
- The backend freezes successfully in an isolated environment (approximately 55 MB before adding scientific/AI modules). The frozen process starts and imports a synthetic OME stack without an external Python process.
- GitHub checks pass on Windows, macOS and Linux for the initial foundation.
- Both unsigned macOS ARM64 DMG and Windows x64 installer packaging jobs passed for development tag `v0.1.0-dev.1`: https://github.com/mansonmyr/OrganelleScope/actions/runs/38868850650

The installers are development artifacts, not the requested comprehensive release. They do not contain the local LLM, denoising/restoration models, full colocalization/inference engine, segmentation workflows or biological evidence integrations. Native installation tests of the generated artifacts and external-machine/GPU tests remain outstanding. A Parallels functional check does not substitute for native Windows x64 hardware testing.

Frontend dependency installation reported zero audit findings after updates. Desktop build tooling reported moderate-severity findings and requires further review before a public production release. Signing credentials are not available; no Developer ID signing/notarization or Windows publisher certificate is claimed.

The release scope and remaining scientific validation gates are tracked in DEVELOPMENT_PLAN.md. Neither a passing build nor an attractive reconstruction establishes accuracy of inferred nanoscale structure.

## ROI restoration verification

Six additional backend tests cover analytic Pearson/Spearman/overlap/Manders cases, undefined constant-channel cases, polygon boundaries and intersection rejection, circle masks, signed/collinear regression, automatic thresholds versus an independent brute-force pixel search, and authenticated API persistence on the correct native Z plane. Saved analyses are rejected after calibration settings change. Three interface tests cover circle completion, explicit polygon completion, Z-specific visibility and disabling drawing during calculation. Browser verification uses generated synthetic images only; biological validation against real experiments and independent software remains outstanding.

## Publication-readiness gate

The current development build is **not yet publication validated**. Exported analyses record this status. Numerical comparisons of Pearson and Spearman against SciPy span 8/16-bit ranges, independent/positive/negative relationships and tied values (absolute tolerance 1e-12). A separate analytic orthogonal-predictor fixture verifies signed standardized regression coefficients and their ratio. The frozen backend has passed a native synthetic OME-TIFF import and six-pair ROI analysis smoke test. These are engineering checks, not substitutes for the following release gates:

| Requirement | Current evidence | Remaining gate |
|---|---|---|
| Formula correctness | Analytic fixtures and SciPy correlation comparisons | Independent Fiji/Coloc 2 comparison using matched masks and threshold conventions |
| Acquisition validity | Metadata provenance and explicit scale confirmation | Check saturation, bleed-through, channel displacement and noise on representative acquisitions |
| Biological interpretation | No binding-probability or causal claim | Blinded positive and negative controls; registration sensitivity where calibration data are unavailable |
| Robust inference | Descriptive measures only | Spatially valid null models, uncertainty calibration and experiment-level replicate analysis |
| Reproducibility | Source hashes, ROI geometry, thresholds, native intensities, algorithm version exported | Versioned benchmark datasets, sample-specific methods reporting and independent review |

Reference guidance: [Dunn, Kamocka & McDonald, 2011](https://pmc.ncbi.nlm.nih.gov/articles/PMC3074624/), [Fiji Coloc 2](https://imagej.net/plugins/coloc-2), and [reproducible microscopy methods reporting](https://www.nature.com/articles/s41592-021-01156-w). The Costes-style implementation has explicitly documented differences and must not be described as identical to Fiji or as implementing the Costes randomization significance test. Pixels, adjacent Z planes and multiple ROIs from one cell must not be presented as independent biological replicates.
