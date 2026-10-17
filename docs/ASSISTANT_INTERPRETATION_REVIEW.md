# Local Gemma interpretation review — 18 October 2026

The active Gemma 4 12B QAT Q4_0 weights were retained. All cases use invented report fixtures and cached-evidence-shaped public identifiers, not microscopy samples or live database calls. No model was downloaded, trained, replaced or given image pixels. These observations assess the application plus prompt/context, not model weights in isolation. One sampled answer per scenario cannot establish an accuracy rate.

| Scenario | Initial result | Developer review |
|---|---|---|
| Constant/all-zero channel | Accepted draft | Correctly distinguished an undefined correlation from calculation failure and biological absence; correctly said threshold changes cannot restore variation. Its generic mention of extreme saturation was poorly matched to the supplied all-zero channel. |
| Threshold-mask proximity | Accepted draft | Rejected binding proof, explained image-scale foreground proximity and boundary truncation, and suggested enlarging/reviewing the cuboid. It did not independently validate the mask or quantify the bias. |
| KEGG membership and knockdown | Accepted draft | Distinguished membership from activation and labelled predicted outcomes hypothetical. No actual pathway mechanism, direction or cell-specific effect was established. Suggested outcomes remained generic rather than evidence for a specific mechanism. |
| Likelihood ratio and Bayes | Request timed out | Operational failure; no answer scored as correct. This is preserved in the initial JSON. |

The guide was then refined to state that high-intensity saturation does not explain an all-zero recorded range. A separate retry completed the constant-channel case in 110.02 seconds and the likelihood/Bayes case in 134.41 seconds overall. The latter may include multiple model calls; this total does not imply a single call exceeded the former two-minute request limit.

The constant-channel retry retained the correct mathematical explanation without the earlier saturation suggestion. The Bayes retry rejected direct conversion, required a prior and an appropriate binding-specific model, and distinguished colocalization from binding. This is an acceptable qualitative explanation for the narrow question; it is not an implementation or validation of a molecular-binding posterior. A fitted Gaussian likelihood-ratio statistic should also not be casually equated to a Bayesian marginal-likelihood ratio (Bayes factor).

The production client's completion timeout is now five minutes per call, verified in the request-configuration test. This is an operational allowance, not a demonstrated scientific improvement; the recorded retry ran with the earlier client timeout. Model calls remain bounded in number, read-only, local and subject to citation/identifier/numeric-format checks. Those checks do not establish semantic correctness. The short status-probe timeout is unchanged.

The assistant now displays deterministic application notes alongside prose; these notes can remain useful when a model draft is too generic. It receives matching segmentation/cuboid/experiment context and selected cached evidence, but no microscopy pixels. Do not call it a vision system or claim it discovered an organelle, inferred binding, validated a mask or predicted a measured knockdown effect.

Records: [initial run](ASSISTANT_INTERPRETATION_BENCHMARK.json), [separate follow-up](ASSISTANT_INTERPRETATION_FOLLOWUP.json), [synthetic harness](../scripts/validation/evaluate_interpretation.py). The harness refuses to load a second model when the development service reports an active one; it unloads its owned process and does not clean weights or projects. Further qualification needs repeated sampling, independent expert review, realistic held-out reports, adverse inputs, native Windows runtime measurements and a predefined scoring rubric.
