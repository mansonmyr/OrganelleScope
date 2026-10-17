# Verification status

OrganelleScope is a research preview. Numerical agreement, installer integrity and biological validity are separate properties. No passing check certifies a biological conclusion or publication readiness.

| Check | Available evidence and limits |
|---|---|
| Deterministic calculations | Backend tests cover correlations, undefined channels, ROI/cuboid containment, processing, batch exports, inference and report provenance. Frontend tests cover interactions and coordinate mapping. Each installer build reruns both suites. |
| Independent Fiji comparison | [36 manual-threshold cases](validation/COLOC2_THRESHOLD_BENCHMARK.json) pass at tolerance 1e-10 after matching strict threshold predicates. Twelve deliberate equality-boundary differences remain recorded. Automatic Costes search/randomization and JaCoP equivalence are not established. [Earlier zero-threshold fixtures](validation/COLOC2_BENCHMARK.json) are preserved. |
| Experiment-level inference | [Hierarchical simulation](validation/HIERARCHICAL_SYNTHETIC_BENCHMARK.json) and [Gaussian simulation](validation/INFERENCE_SYNTHETIC_BENCHMARK.json) document finite-sample limitations. Bootstrap intervals can under-cover; pixels are not independent biological replicates. |
| Assistant interpretation | [Initial synthetic assessment](validation/ASSISTANT_INTERPRETATION_BENCHMARK.json), [follow-up](validation/ASSISTANT_INTERPRETATION_FOLLOWUP.json) and [full model decision record](../README_MODEL_DECISIONS.md) retain errors and timeouts. These are sampled drafts, not a biomedical accuracy estimate. |
| Build integrity | Release assets include SHA-256 checksums and platform verification records. Packaging tests the frozen analysis executable; macOS additionally checks the mounted DMG and signatures. [Earlier local 0.2.4 build](validation/BUILD_VERIFICATION_0.2.4.json) and [source checks](validation/SOURCE_VERIFICATION_0.2.4.json) remain historical records, not verification of later binaries. |
| Biological validation | Incomplete. Supplied local microscopy samples support technical investigation, not an independent blinded biological benchmark. Private images and marker assignments are excluded from public evidence. |
| Native installation and scale | Automated packaging is separate from human installation/interaction testing. Windows x64 user acceptance, representative 2048² four-channel workload qualification and Apple notarization remain incomplete. |

Cuboid summaries read only the inclusive X/Y/Z bounds from source voxels, with the explicitly selected raw/processed recipe. They do not summarize an entire stack outside the box. Tests include known signals inside/outside the region, changing Z bounds and translated/resized regions. Threshold objects are mathematical masks rather than validated organelle identities.

For definitions, assumptions, references and reporting guidance, use the [manual](../MANUAL.md). Biological validation remains deferred at the user's request. Do not describe the application or assistant as scientifically certified.
