# OrganelleScope 1.0.6

- Portable HTML analysis review links ROI engine values to embedded source-plane previews and geometry, with calibration, processing and matching 3D/sensitivity records. Source checksums and latest ROI calculation identity are verified before export.
- Interactive ROI analysis runs with stage progress and cooperative cancellation. Switching/restoring workspaces cancels the previous job and prevents late results from replacing the new view. Earlier completed results survive cancellation/failure. Reusing a TIFF directory avoids repeated parsing while retaining one Z plane's channels at a time.
- Batch queues add next-unreviewed navigation and separate recovery drafts for failed/unfinished images. Original runs remain unchanged, metadata changes clear review, and recovery provenance appears in Excel/full JSON.
- Assistant measurement tools use filtered reports, stale ROI/threshold settings are excluded, and deterministic notes explain overlapping signals with negative intensity covariance.
- Native service checks isolate the complete profile, including sibling project storage, so repeated checks cannot reuse another test run’s saved projects.
- Installer packaging audits reject research TIFF/storage payloads. Native startup checks inspect empty image/project/batch/recovery storage for isolated profiles. Upgrades retain each account's own research data.

Download the Apple Silicon macOS `.dmg` or Windows x64 `.exe`. The inference runtime is bundled; Gemma weights are downloaded once during setup. See the [manual](../MANUAL.md) and [verification scope](VALIDATION.md).
