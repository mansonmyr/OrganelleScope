# OrganelleScope 1.0.2

This update improves the interpretation and verification of image-based 3D proximity.

- Separate marker-to-reference and reference-to-marker summaries report the source voxel count, count/fraction within the selected distance, minimum, median and 95th percentile. Existing forward export fields remain compatible.
- Calibration uses separate Z/Y/X spacing. Reports expose search-domain, mask definitions and cuboid-face voxel counts; empty masks have an explicit unavailable reason.
- Sixty synthetic geometries agree with an independent exhaustive pairwise-distance oracle in both directions. API tests check full Z signal and reference containment within the chosen cuboid.
- A separate report-backed findings section, deterministic assistant notes and recorded quantities explain direction, existing reverse summaries and empty cropped masks. Stronger local negation and quotation-topic checks address specific overclaims.
- New synthetic assistant questions, developer claim-level review and targeted follow-up/replay records distinguish useful answers, omissions and unsupported statements. These diagnostics are separate from a general biomedical accuracy benchmark.

The existing compact workspace layout, background subtraction, Gaussian smoothing, local Gemma setup, per-channel LUTs and native-range preview remain available. New users start with empty research storage; upgrades preserve their own data. Download the Apple Silicon Mac `.dmg` or Windows x64 `.exe` below. Gemma weights use a resumable one-time 6.98 GB download; inference then runs locally.

See the [manual](../MANUAL.md) and [verification scope](VALIDATION.md) for definitions, references and evidence. Voxel-centre distances describe threshold-defined image geometry, rather than molecular binding or super-resolution accuracy. AI drafts require human review.
