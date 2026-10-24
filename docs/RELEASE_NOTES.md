# OrganelleScope 1.0.8

Download **OrganelleScope-1.0.8-macos-arm64.dmg** for Apple Silicon Macs, or **OrganelleScope-1.0.8-windows-x64.exe** for Windows. Only the installer for your platform is needed. The other assets provide checksums, dependency notices and build verification records.

- Added raw ROI clipping counts and warnings. Line-profile widths are withheld when contributing raw samples reach the storage ceiling.
- Added threshold occupancy, automatic-threshold method diagnostics and per-ROI background variation. The curved-kernel lower-envelope estimator is named explicitly, with separate spatial radius and intensity-height guidance.
- Added 3D mask occupancy, boundary and axial-sampling diagnostics alongside directed proximity measurements.
- Small-sample comparisons report estimation-only status when their exact permutation design cannot attain 0.05. Sample standard deviation is separate from Gaussian MLE; exploratory bootstrap intervals require opt-in.
- Strengthened assistant checks for unsupported background explanations, context-dependent claims and claims of true colocalization. Generated interpretations still require scientific review.
- Preserved earlier ROI reports as individually exportable versions. Updated the manual and recorded an 800-simulation small-sample assessment.

Fresh installations start with empty research storage; upgrades preserve your existing images, projects and reports. Personal research data is not included in either installer.

The local inference runtime is included. **Gemma weights download automatically during first-use setup** with pinned size and SHA-256 verification; the approximately 7 GB weights are not inside the installers. An internet connection is required for that initial download, after which inference runs locally.

The macOS installer is ad-hoc signed and not notarized; the Windows installer is unsigned. See the [manual](../MANUAL.md) and [verification records](VALIDATION.md) for installation, methods and interpretation limits.
