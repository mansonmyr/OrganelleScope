# Foundation verification — 16 October 2026

This records engineering checks for the first milestone. It is not a biological validation certificate.

- 25 backend tests pass in an isolated environment. Coverage includes OME/ImageJ scale extraction, generic print-DPI refusal, source identity, persistent-record refresh, axis confirmation, all C/Z planes, compressed/endian variants and bounded calibrated volume geometry.
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
