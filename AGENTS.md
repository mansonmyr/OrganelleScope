# OrganelleScope maintenance preferences

The user requests conservative cleanup throughout development to save disk space.

- Keep one active assistant model. Remove explicitly superseded model weights only after the replacement has passed integrity and real inference checks.
- Remove obsolete downloaded runtime archives, temporary evaluation logs and generated scratch files after verification. Keep the active runtime and required dependencies.
- Keep small, reproducible evaluation summaries and source history. Avoid retaining duplicate multi-gigabyte installers/builds without a reason; identify exact obsolete generated artifacts before removal.
- Preserve imported microscopy images, saved projects, ROIs, measurements, conversations, scientific evidence and user exports. Do not treat these as disposable cache. Evidence already has a bounded cache; offline research data has value.
- Cleanup must stay within this application's managed directories. Never sweep the user's Downloads, other repositories, global package caches or unrelated files.
