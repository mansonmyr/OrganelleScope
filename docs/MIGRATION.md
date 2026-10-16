# Source migration

Initial comparison on 2026-10-16:

| Source | GitHub HEAD | Compared files |
|---|---|---|
| mansonmyr/Probabilistic_Colocalization_Estimator | `dafe53fe22d8c7c2874bbab446b943c83b5c0c8f` | 92 identical, 4 different, 13 GitHub-only |
| mansonmyr/Quick-IF-Line-Profiler | `2d93039274c7ab97916c9f1979a3c63a84812ce0` | 22 identical, 1 different, 2 GitHub-only |

Comparison accounts for the differing PCE layouts: local `backend/app`, `backend/tests`, `frontend/src` and Electron/script folders map to GitHub root equivalents. The local folders did not contain Git histories.

Full remote Git mirrors, local source snapshots and file-level comparison/SHA-256 manifests are preserved in the sibling `migration-archives` directory outside the new repository. That archive includes local sample data and is **not uploaded**. The original directories are unchanged apart from any test-runner temporary caches created during the earlier assessment. Do not delete originals until archive verification and the complete migration are accepted.

Selected Quick IF Line Profiler chart, TIFF-chart export, profile types and analysis helpers have been migrated with notices. Fractional sample-index crossings now map through actual sampled pixel distances for FWHM, and profile smoothing uses a fixed approximate physical pixel window rather than a fraction of ROI length. Imported legacy preprocessing/classification helpers remain unvalidated compatibility code and are not offered by the new UI.

The PCE model wrapper, mock classifier and discovery score are not adopted into the new measurement engine. The new TIFF import module is a replacement, not a claim that all original features have been merged already.
