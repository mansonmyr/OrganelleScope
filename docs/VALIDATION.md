# Verification status

OrganelleScope 1.0 is released for the documented local research workflows. Numerical agreement, installer integrity and biological validity are separate properties. No passing check certifies a biological conclusion or publication readiness.

| Check | Available evidence and limits |
|---|---|
| Deterministic calculations | Backend tests cover correlations, undefined channels, ROI/cuboid containment, processing, batch exports, inference and report provenance. Frontend tests cover interactions and coordinate mapping. Each installer build reruns both suites. |
| Independent Fiji comparison | [36 manual-threshold cases](validation/COLOC2_THRESHOLD_BENCHMARK.json) pass at tolerance 1e-10 after matching strict threshold predicates. Twelve deliberate equality-boundary differences remain recorded. Automatic Costes search/randomization and JaCoP equivalence are not established. [Earlier zero-threshold fixtures](validation/COLOC2_BENCHMARK.json) are preserved. |
| Experiment-level inference | [Hierarchical simulation](validation/HIERARCHICAL_SYNTHETIC_BENCHMARK.json) and [Gaussian simulation](validation/INFERENCE_SYNTHETIC_BENCHMARK.json) document finite-sample limitations. Bootstrap intervals can under-cover; pixels are not independent biological replicates. |
| Assistant interpretation | [Initial synthetic assessment](validation/ASSISTANT_INTERPRETATION_BENCHMARK.json), [follow-up](validation/ASSISTANT_INTERPRETATION_FOLLOWUP.json) and [full model decision record](../README_MODEL_DECISIONS.md) retain errors and timeouts. These are sampled drafts, not a biomedical accuracy estimate. |
| Build integrity | Release assets include SHA-256 checksums and platform verification records. Packaging tests the frozen analysis executable; macOS additionally checks the mounted DMG and signatures. [Earlier local 0.2.4 build](validation/BUILD_VERIFICATION_0.2.4.json) and [source checks](validation/SOURCE_VERIFICATION_0.2.4.json) remain historical records, not verification of later binaries. |
| Biological validation | Incomplete. Supplied local microscopy samples support technical investigation, not an independent blinded biological benchmark. Private images and marker assignments are excluded from public evidence. |
| Native installation and scale | Automated packaging is separate from human installation/interaction testing. Release candidates include native startup/install checks and synthetic 2048² four-channel frozen-service workloads on both platforms. Human Windows x64 acceptance and representative acquisition qualification remain incomplete; trusted publisher signing is excluded from the requested scope. |

Cuboid summaries read only the inclusive X/Y/Z bounds from source voxels, with the explicitly selected raw/processed recipe. They do not summarize an entire stack outside the box. Tests include known signals inside/outside the region, changing Z bounds and translated/resized regions. Threshold objects are mathematical masks rather than validated organelle identities.

For definitions, assumptions, references and reporting guidance, use the [manual](../MANUAL.md). Owner-supplied samples are being used for local control checks; a blinded population-level benchmark is not established. Do not describe the application or assistant as scientifically certified.

## Current 0.2.6 checks

- [Statistical oracles](validation/STATISTICAL_ORACLES_0.2.6.json): exact independent rational enumeration for paired/independent permutation examples, and prior importance sampling of a Gaussian model against the closed-form Bayesian posterior. These are numerical cross-checks, not coverage or biological certification.
- [Download resume probe](validation/MODEL_DOWNLOAD_RESUME_0.2.6.json): a bounded live request for the last 64 KiB matches the pinned local Gemma file. Download/resume/corruption/cancellation/binary-byte handling also have deterministic tests. The probe is not a new full-weight download.
- [Initial unseen assistant questions](validation/ASSISTANT_UNSEEN_0.2.6.json): all four initial drafts were withheld. This exposed overly restrictive review checks; withholding is not scientific success. Follow-up runs after changes are labelled as follow-ups rather than new unseen questions.
- Owner-supplied samples are analysed locally with hash-bound marker assignments, proposed reference-channel ROIs and predefined threshold/size sensitivity. Private images, annotations and measured results are excluded from Git. ROI selection, image-specific expected-pattern consistency and population-level inference are separate properties.
- Trusted publisher signing is outside the requested scope. Development signature/integrity checks are retained. Native startup/installer extraction and frozen-service workloads are recorded per release; human acceptance remains a separate check.

The initial audit was refined after failure analysis. [Follow-up diagnostics](validation/ASSISTANT_AUDIT_FOLLOWUP_0.2.6.json) include a retained scientific error; [targeted follow-up](validation/ASSISTANT_GROUNDED_FOLLOWUP_0.2.6.json) and [scope replay](validation/ASSISTANT_SCOPE_REPLAY_0.2.6.json) record later changes without rebranding repeated questions as unseen. Same-model checking is not independent scientific review.

[Full-size setup verification](validation/FULL_WEIGHT_SETUP_0.2.6.json) uses the existing pinned model bytes through a temporary hard link, avoiding another download/disk copy. It verifies the complete SHA-256 and atomic installation/relaunch state, not a fresh full network transfer. [Local native-stack observations](validation/NATIVE_STACK_MACOS_0.2.6.json) cover a decoded 1 GiB synthetic 32-slice stack while a Gemma assessment was active. All four channel cuboid sums agree exactly; timings are not an isolated hardware comparison. Release assets provide separate build-specific platform checks.

Owner annotation corrections can supersede specimen interpretations even when source hashes and numerical calculations remain unchanged. Two private sample assignments were corrected after owner review on 18 October 2026; reference-based ROIs and reports were rerun where needed. Earlier model diagnostics retain their historical input labels and are not biological ground truth. The public repository contains no private marker map or specimen measurements.


## Current 0.2.7 checks

Batch channel-correction tests verify review invalidation, preservation of ROI geometry and immutability of earlier runs. Design tests cover nested cell counts, missing labels and repeated-source conflicts; Excel includes the review without changing raw measurements. These checks prevent specific provenance/pseudoreplication errors, not verify culture independence.

Local candidate reports now retain explicit owner-accepted/rejected statuses. Only accepted regions may support the scoped control review; rejected candidates remain as technical results. The available accepted subset does not establish negative-control discrimination or population-level specificity. Source images and detailed decisions remain private.

[New interpretation diagnostic](validation/ASSISTANT_RELEASE_QUESTIONS_0.2.6.json) and [corrected follow-up](validation/ASSISTANT_RELEASE_FOLLOWUP_0.2.6.json) preserve an inconsistent synthetic fixture and an overconfident annotation claim. Repeated questions are labelled follow-ups. Same-model audit can retain scientifically unsupported prose; no overall accuracy rate is inferred.

[Local 0.2.7 frozen-service workload](validation/NATIVE_STACK_MACOS_0.2.7.json) checks a decoded 1 GiB, 32-slice, four-channel stack and three sequential technical-repeat imports. Cuboid and batch channel sums match exact source expectations; copied sources are flagged. Process-tree RSS includes the driver and service. The synthetic timings and memory are not a real-acquisition distribution or general hardware guarantee.

[Local installer observations](validation/NATIVE_INSTALL_OBSERVATIONS_0.2.7.json) retain an initial temporary-copy launch failure, a successful direct launch and a successful full installer recheck. The original failure cause is not isolated; verifier diagnostics now expose child errors. This candidate is not a claim of failure-free startup.


## Stable release 1.0 qualification

Stable publication requires platform reports for both installers: exact artifact hashes, native runtime execution, repeated native startup (two fresh profiles and one retained profile), authenticated service readiness, renderer paint, observed owned-backend shutdown, and exact stack/batch sums with copied-source detection. Tests also exercise deliberately failed readiness/spawn, bounded shutdown, log rotation/redaction, and model-free summaries after withheld AI drafts. Frozen-service checks include ROI correlation, source-preserving channel names, project save/reopen and a model-free summary. These are operational and numerical release criteria, not certification of a specimen or generated interpretation.

The 0.2.7 one-off local launch failure remains a historical observation; its original hidden error cannot be reconstructed retrospectively. No definite root cause is claimed. Version 1.0 adds diagnostics and addresses concrete readiness/shutdown weaknesses; repeated fresh and retained-profile qualification is required for the new artifacts. Historical failure records are retained rather than deleted or retroactively marked fixed.

Core measurement definitions, independent numerical comparisons and scientific assumptions remain documented. The AI component is optional assistive interpretation, with explicit review status and deterministic summaries available independently. A stable software release does not imply an error-free LLM, independent biological replication, negative-control discrimination or a publication certificate.

[Exact local 1.0 installer qualification](validation/STARTUP_QUALIFICATION_1.0.0.json) records nine successful launches (six fresh, three retained profiles), observed backend exits and frozen analysis/project/summary checks. [The local 1 GiB stack and batch record](validation/NATIVE_STACK_MACOS_1.0.0.json) checks exact source sums. Release assets contain independent build-specific qualification records for the distributed Mac and Windows installers.
