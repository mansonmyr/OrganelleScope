# OrganelleScope 1.0.3

- ROI linear-size/manual-threshold and 3D cuboid-boundary/threshold sweeps compare explicitly recorded settings without choosing a preferred result. Undefined/clamped variants remain visible; exports preserve the complete comparison.
- Acquisition checks accept optional nominal lateral/axial resolution and a native-unit detector ceiling. Reports distinguish missing/conflicting calibration, coarse sampling, possible clipping and unmeasured registration. Signal counts describe the selected plane, not an entire stack.
- Experiment comparisons expose experiment/cell/ROI/source counts and reject repeated raw-source ROI geometry despite renamed IDs or equivalent polygon/circle parameterization. Biological independence remains a property of the experimental design.
- The assistant adds separate question-coverage review after claim/source review. Four controlled complete/incomplete answer pairs matched expected labels; this is a bounded diagnostic, not general model accuracy. Coverage failures do not prevent asking questions or discard usable drafts.
- The manual includes detailed workflows, interpretation, limits and primary references for these additions.

Download the Apple Silicon macOS `.dmg` or Windows x64 `.exe`. The compact interface, local Gemma setup, native-range previews and existing research data remain compatible. First installations have empty research storage; upgrades preserve the account's data and verified model weights. See the [manual](../MANUAL.md) and [verification scope](VALIDATION.md).
