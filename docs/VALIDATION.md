# Verification and scientific scope

OrganelleScope 1.0 is a local research release. This page separates established checks from the scientific interpretation that each experiment must justify.

## Current release qualification

Both platform installers pass build-specific gates for artifact checksums, bundled runtime execution, repeated native startup with fresh and retained profiles, authenticated analysis-service readiness, renderer paint, observed backend shutdown and exact stack/batch sums. Frozen-service checks cover ROI correlation, channel identity, project save/reopen and model-free analysis summaries. The distributed installers have their own verification assets under [Releases](https://github.com/mansonmyr/OrganelleScope/releases).

The [local Mac installer record](validation/STARTUP_QUALIFICATION_1.0.0.json) documents nine successful launches: six fresh profiles and three retained profiles. The [local 1 GiB stack record](validation/NATIVE_STACK_MACOS_1.0.0.json) checks a 32-slice, 2048², four-channel synthetic stack and three sequential technical-repeat imports against exact source sums. These workloads describe tested configurations, rather than a universal memory or speed guarantee. Native automation and human acceptance testing are distinct. macOS uses ad-hoc signing; Windows has no publisher certificate.

New-account installations use separate local application storage and start without imported images or saved projects. Upgrades preserve the existing account’s research data. The updated source adds native smoke checks that explicitly inspect the image/project lists before test interactions; model setup adds weights rather than sample images.

## Numerical and workflow evidence

| Area | Evidence and scope |
|---|---|
| ROI and 3D measurements | Tests cover correlation, constant/empty channels, threshold conventions, processing, exports, and inclusive cuboid containment. Cuboids read only source voxels within their selected X/Y/Z bounds, including translated and resized regions. Threshold masks describe mathematical objects; biological identities require review. |
| Fiji comparison | [36 matched manual-threshold cases](validation/COLOC2_THRESHOLD_BENCHMARK.json) agree within 1e-10. Twelve deliberate threshold-equality differences are recorded. [Earlier zero-threshold cases](validation/COLOC2_BENCHMARK.json) remain available. This comparison covers the tested definitions, not automatic Costes search/randomization or every JaCoP function. |
| Experiment-level inference | [Hierarchical simulations](validation/HIERARCHICAL_SYNTHETIC_BENCHMARK.json), [Gaussian simulations](validation/INFERENCE_SYNTHETIC_BENCHMARK.json) and [independent numerical oracles](validation/STATISTICAL_ORACLES_0.2.6.json) document assumptions and finite-sample behavior. Bootstrap intervals can under-cover; pixels and copied images are not independent biological replicates. |
| Local biological samples | Owner-reviewed regions support scoped workflow checks. Rejected regions remain identified in private technical reports. The accepted subset supports neither negative-control discrimination nor population-level specificity. Private images, assignments and measurements are excluded from Git. |
| Model setup | [Full-weight integrity/setup](validation/FULL_WEIGHT_SETUP_0.2.6.json) checks existing pinned bytes through a temporary hard link and atomic installation. [A live range request](validation/MODEL_DOWNLOAD_RESUME_0.2.6.json) checks a final 64 KiB segment; it is not a second full download. Deterministic tests exercise resume, cancellation and corruption handling. |

## Directed 3D proximity checks

[Sixty synthetic geometries](validation/PROXIMITY_ORACLE_1.0.2.json) compare both directed summaries against exhaustive physical-coordinate pairwise distances, with a 1e-12 µm tolerance for distance summaries and matching threshold counts/fractions. Tests cover anisotropic Z sampling, inclusive threshold equality, overlapping/empty masks, translation/unit scaling and source-API cuboid containment. Including or excluding an outside reference signal changes the result as expected. The reference search is intentionally limited to the selected cuboid. Numerical agreement does not establish molecular-distance accuracy, registration quality or organelle-specific biological validity. See [SciPy's EDT definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.distance_transform_edt.html) and the manual for interpretation.

## Assistant interpretation

Gemma produces optional drafts; engine-derived values and deterministic summaries remain separate. Same-model source review can miss unsupported scientific claims. A returned draft count is not a correct-answer rate. Evaluate interpretation against the actual measurements, cited source payloads and experimental design.

The [model decision record](../README_MODEL_DECISIONS.md) preserves questions, outputs, observed errors and changes across model profiles. [Initial questions](validation/ASSISTANT_UNSEEN_0.2.6.json), [follow-up diagnostics](validation/ASSISTANT_AUDIT_FOLLOWUP_0.2.6.json), [release questions](validation/ASSISTANT_RELEASE_QUESTIONS_0.2.6.json) and [corrected follow-up](validation/ASSISTANT_RELEASE_FOLLOWUP_0.2.6.json) retain their original assessment conditions. [Annotation replay](validation/ASSISTANT_ANNOTATION_REPLAY_0.2.7.json) is a deterministic guard replay, not another model inference. General biomedical accuracy is not inferred from these small assessments.

## Historical records

Files under `docs/validation/` are versioned evidence, including original unsuccessful checks and superseded fixtures. Their version and scope matter; they are not current feature requirements. The [0.2.7 startup observation](validation/NATIVE_INSTALL_OBSERVATIONS_0.2.7.json) records an initial failure and successful subsequent checks. Its hidden original error was not recovered. Version 1.0 adds readiness/shutdown hardening and diagnostic logs, with the new artifact qualified separately. Earlier outcomes are preserved without a retrospective root-cause claim.

Use the [manual](../MANUAL.md) for definitions, assumptions, reporting guidance and original references. Stable software qualification supports reproducible research workflows; biological conclusions still depend on acquisition quality, controls and independent experimental design.

## Assistant proximity assessment

[Four initial synthetic questions](validation/ASSISTANT_PROXIMITY_INITIAL_1.0.2.json) have criteria frozen before inference. The [developer claim-level review](validation/ASSISTANT_PROXIMITY_REVIEW_1.0.2.json) records unnecessary rerun advice, an incomplete empty-reference answer, an inadequately supported dimensional explanation, and a fully withheld annotation-instruction answer. A [targeted follow-up](validation/ASSISTANT_PROXIMITY_FOLLOWUP_1.0.2.json) repeats two questions after changes; it is not a fresh unseen assessment. Both follow-up drafts remain incomplete; the review records their omissions. Current application findings present the necessary report status separately from AI prose. A [single-claim replay](validation/ASSISTANT_PROXIMITY_QUOTE_REPLAY_1.0.2.json) withholds the original insufficiently supported explanation without new model inference.

A [forced-acceptance guard baseline](validation/CLAIM_GUARD_BASELINE_1.0.2.json) and [targeted replay](validation/CLAIM_GUARD_REPLAY_1.0.2.json) isolate deterministic behavior on eleven developer-labelled adversarial sentences. The deliberately permissive stub reviewer is not Gemma. All eleven expected outcomes match after the change, including ordinary supported statements; this result is not a model accuracy score or proof of general citation entailment.
