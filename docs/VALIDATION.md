# Verification and scientific scope

OrganelleScope 1.0 is a local research release. This page separates established checks from the scientific interpretation that each experiment must justify.

## Current release qualification

Both platform installers pass build-specific gates for artifact checksums, bundled runtime execution, repeated native startup with fresh and retained profiles, authenticated analysis-service readiness, renderer paint, observed backend shutdown and exact stack/batch sums. Frozen-service checks cover ROI correlation, channel identity, project save/reopen and model-free analysis summaries. The distributed installers have their own verification assets under [Releases](https://github.com/mansonmyr/OrganelleScope/releases).

The [local Mac installer record](validation/STARTUP_QUALIFICATION_1.0.0.json) documents nine successful launches: six fresh profiles and three retained profiles. The [local 1 GiB stack record](validation/NATIVE_STACK_MACOS_1.0.0.json) checks a 32-slice, 2048², four-channel synthetic stack and three sequential technical-repeat imports against exact source sums. These workloads describe tested configurations, rather than a universal memory or speed guarantee. Native automation and human acceptance testing are distinct. macOS uses ad-hoc signing; Windows has no publisher certificate.

New-account installations use separate local application storage and start without imported images or saved projects. Upgrades preserve the existing account’s research data. The updated source adds native smoke checks that explicitly inspect the image/project/batch/recovery lists before test interactions; model setup adds weights rather than sample images.

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

## Settings, acquisition, replication and coverage checks

The [workflow regressions](../backend/tests/test_sensitivity_quality_replication.py) compare ROI pixel counts and thresholded fractions with direct pixel expectations, retain empty-reference sweep variants, check nominal sampling and declared detector counts, and test experiment weighting plus equivalent/renamed geometry duplication. The [coverage regressions](../backend/tests/test_completeness.py) reject fabricated spans, incomplete/duplicate mappings and unbounded completeness claims. Frozen-service checks now exercise both sweep endpoints and optional acquisition parameters in the packaged executable.

[Four fixed answer pairs](validation/COMPLETENESS_REVIEW_1.0.3.json), frozen before local Gemma review, compare deliberately complete and incomplete answers. All four matched the developer labels for the identified request parts. This measures a small controlled coverage diagnostic, not response generation quality, biomedical accuracy or independent citation entailment. Same-model coverage can still overlook compound requirements or incorrectly judge relevance.

## Review, recovery and responsiveness checks (1.0.4–1.0.6)

Regression tests cover asynchronous/synchronous ROI numerical parity, cancellation preserving previous results, source-checksum refusal, escaped HTML/embedded ROI geometry, altered-result exclusion, separate failed-item recovery with metadata review, exact TIFF-directory reuse and exclusion of stale assistant ROI/sensitivity records. Interface regression tests also restore a different image while a calculation response is held, then deliver that late response and verify that it cannot replace the new workspace. Package audits check both resource trees and application archive entries for research TIFFs/storage. Both native frozen-service jobs exercise asynchronous analysis and portable report generation; desktop checks inspect all four fresh-profile storage categories. Consult each release's verification assets for its actual gate results.

The [bounded reader benchmark](validation/ROI_READER_1.0.4.json) compares per-plane directory opening with directory reuse in isolated processes. All engine outputs match exactly. Timings and sampled RSS depend on system/cache conditions; no universal speed or memory improvement is asserted.

The [initial four-question workflow assessment](validation/WORKFLOW_ASSISTANT_1.0.4.json) returned partial or withheld answers in every case; the automatic coverage review flagged each as incomplete. After explicit workflow definitions were added, the [two-question follow-up](validation/WORKFLOW_ASSISTANT_FOLLOWUP_1.0.4.json) directly addressed sensitivity selection and recovery/replication. This is developer qualitative review of single sampled answers. The repeated questions are not an unseen accuracy benchmark, and the initial limitations remain visible. No private microscopy images or cloud inference were used.

## Expanded performance coverage (1.0.7)

[Real/synthetic HTTP workload](validation/PERFORMANCE_COVERAGE_1.0.7.json): four local real TIFFs, a 2 GiB decoded synthetic stack and 30 technical repeats. Source hashes remain unchanged; exact ROI counts/sums and defined Pearson values agree with independent native-page crops/SciPy. All repeats complete and export to Excel, while source duplication remains flagged. Detailed private records are excluded from Git. The public record reports a supervised 768 MiB service RSS budget on a 24 GB Mac, separate driver RSS and readiness latency. It excludes Gemma and does not emulate a low-memory computer.

[Linux CI qualification](https://github.com/mansonmyr/OrganelleScope/actions/runs/39132387323/job/117690023385) passed the new worker under an enforced 1.5 GiB virtual-address-space cap. The worker checks exact preview/ROI values on a 256 MiB decoded synthetic source. Mac and Windows source tests also run the source-plane lifetime and pixel-parity regressions; packaged-native workload checks are separate. A physically lower-memory Mac/Windows installation remains a separate hardware test.

## Broader assistant assessment (1.0.7)

The [twelve-question record](validation/ASSISTANT_BROADER_1.0.7.json) preserves the pre-inference manifest, its hash and source commit, implementation hashes, actual tool/claim audits and developer review. These are new formulations of overlapping development concepts, not an external blinded scientific benchmark. Nine initial answers were judged complete, two partial and one misleading. All twelve were marked addressed by automatic coverage, demonstrating that completeness flags cannot certify scientific correctness.

The misleading answer accepted an embedded instruction as an activation annotation. The partial answers ambiguously described the threshold operand and omitted the practical instruction to change a cropped region and recalculate. Revised definitions and targeted guards address the observed constructions. Forced-acceptance regression tests check that ambiguous/activation claims are withheld while explicit threshold definitions and ordinary denials remain eligible. The complete curated reference tail remains available within the fixed total reviewer context budget. No keyword guard establishes general entailment.

An identity/rating-withheld randomized packet is available locally for independent review. No independent human reviewer was available; this status remains pending. Private samples are absent from these synthetic assistant inputs. Original results are retained separately from any repeated follow-up.

The [matched volume-memory comparison](validation/VOLUME_MEMORY_COMPARISON_1.0.7.json) records approximately 1,055 MiB versus 564 MiB sampled peak service RSS before/after releasing source-plane views, for the same decoded synthetic geometry and workload options. Both pass the independent ROI oracle. This single-run comparison does not include Gemma and makes no universal memory/speed claim.

The [three-question follow-up](validation/ASSISTANT_TARGETED_FOLLOWUP_1.0.7.json) uses the original frozen questions and records implementation hashes separately. The annotation answer clearly rejects instruction-derived activation; two displayed drafts remain partial (missing direction detail and actionable region-change advice), although automatic coverage marks all addressed. The corrected direction sentence and region-change advice appeared in the draft but were withheld by conservative source review. These outcomes are preserved, not counted as three successes. After the run, deterministic application findings were extended with explicit change-region/recalculate advice for unavailable proximity; regression checks cover its presence for unavailable reports and absence from valid directed summaries. This guidance is independent of the model, not a new model evaluation.


## Source 1.0.8: measurement-quality safeguards

This source update adds selected-region raw ceiling counts, threshold occupancy,
ROI background variation, clipped-line width withholding, finite-cuboid sampling
warnings and preserved ROI-report history. Numerical coefficients retain their
existing definitions; report and method identifiers distinguish the new diagnostics.
Regression tests cover both raw and processed inputs, legacy-report preservation,
malformed history responses, all-positive thresholds, small-sample output and
accepted-by-reviewer assistant counterexamples.

Experiment contrasts whose exact two-sided probability floor exceeds 0.05 are
labelled estimation only. Sample SD and optional Gaussian MLE sigma are separate.
Percentile intervals require an explicit exploratory opt-in. The reproducible
[small-sample assessment](validation/SMALL_SAMPLE_COVERAGE_1.0.8.json) runs the
actual inference routine on one Gaussian null family: 100 realizations per size
and design, three through six experiments, four cells per experiment and 999
bootstrap draws. Its 0.80–0.93 coverage range motivates the default change; it is
not nominal-coverage certification. Reproduce with:

```sh
python scripts/validation/benchmark_small_sample.py --output /path/to/coverage.json
```

The backend suite, interface tests, type check and production UI build assess this
source revision. Installer and native-platform qualification records apply to the
specific installer commit/version named in those records, rather than automatically
to a later source push. Assistant filters address identified failure patterns;
source quotation and same-model review still do not guarantee scientific correctness.

## Python-only replay and expanded interval assessment

The public `python -m organelle_scope.cli demo --output replay/demo.json` command checks closed-form positive/negative correlation, average ranks with ties, strict directional fractions and an anisotropic two-point distance. The `roi` command checks the image digest and replays explicit manifest geometry without Electron, Node.js, a saved project, model or database. See the [README instructions](../README.md#python-only-numerical-replay).

The [expanded assessment](validation/SMALL_SAMPLE_COVERAGE_2000.json) executes the actual opt-in inference routine 2,000 times for each of eight design/size combinations (16,000 analyses), using the same Gaussian nested null family and 999 bootstrap draws. Observed percentile coverage is 0.814–0.9215. Experiment-mean Welch/paired t baselines cover 0.9435–0.966. Binomial intervals describe simulation precision; no general coverage, power or robustness certificate is inferred. Designs unable to attain 0.05 are explicitly marked. This supports keeping percentile intervals exploratory and disabled by default. Reproduce with:

```sh
python scripts/validation/benchmark_small_sample.py --repetitions 2000 --output /path/to/coverage.json
```

Manuscript-specific image results and acquisition metadata belong to the separately shared, hash-identified submission dataset; they are not bundled in installers or silently added to the public repository.
