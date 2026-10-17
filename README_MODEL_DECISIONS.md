# OrganelleScope: cumulative local-model decisions

This README is the accumulating decision record for the local assistant. Keep previous evaluations and their limitations when adding new candidates; append dated decisions rather than rewriting history into a claim that the current model is universally best. Gemma is currently retained as an **experimental, supervised interpreter**, not a validated biological reasoning engine. Measurements and statistical calculations remain in the deterministic application engine.

## Current decision — 17 October 2026

Retain **Gemma 4 12B Instruct, official Google QAT Q4_0**. Do not replace it with the assessed Liquid LFM2.5-8B-A1B Q4_K_M profile. Qwen3.5-4B and Ministral 3 8B remain retired. Only Gemma's weights are retained locally; the small manifests, licences, source history and evaluation records remain available.

This decision weighs observed scientific and task failures above smaller downloads, speed, fluency or vendor benchmark scores. It does not establish that Gemma is more reliable than every Qwen or Liquid model, or that any tested model can independently interpret publication results.

| Evaluated profile | Outcome and rationale | Evidence quality |
| --- | --- | --- |
| Qwen3.5-4B community Q4_K_M, 0.1.7 | Retired after exploratory testing. An early answer confused a pixel-based ROI dimension with physical distance; an unrecognised reference was also produced. These failures motivated separating engine-derived numeric values from model prose, response checks and citation restrictions. | Historical engineering smoke tests; different prompts/guards from later models. No controlled Gemma-versus-Qwen comparison. |
| Ministral 3 8B official Q4_K_M, 0.1.8 | Successfully used local tools and distinguished correlation from binding, but gave generic guidance, confused undocumented controls with absence, and attached unsupported methodological attribution to KEGG evidence. Superseded for further evaluation. | Small development sample. Expanded context and answer budgets were subsequently introduced, so later improvements cannot be attributed solely to model weights. |
| Gemma 4 12B official QAT Q4_0, 0.1.9 | Retained provisionally. Uses saved settings/measurements, can call reference checks and read KEGG evidence, and can distinguish undocumented experiments from experiments never performed. Still makes qualitative scientific/statistical overclaims and sometimes fails response checks. | Initial six cases, two targeted retests, interface persistence check, then a fresh paired eight-case diagnostic comparison with Liquid. No independent biological accuracy benchmark. |
| Liquid LFM2.5-8B-A1B official Q4_K_M | Not selected in this integration. Smaller and generally quicker, but fabricated an active filter and an analysis event, omitted requested reference/evidence tools, claimed available KEGG information was unavailable, and misidentified the covariance-test null as no binding. | Same eight questions, projects, prompt and application safeguards as the fresh Gemma run; different vendor sampling/thinking profiles. One run per case. |

## What the paired Liquid/Gemma run actually showed

The paired run used the same synthetic ROI project (revision 5) and cache-only KEGG project (revision 1), empty histories, the same read-only tool allowlist and the same pre-existing response guards. Six questions repeated earlier tasks; two new questions probed proximity-ligation interpretation and Bayesian conversion of the saved Gaussian statistic. Model weights were verified against pinned upstream checksums. No microscopy images or conversations were transmitted to a cloud LLM.

| Observation | Gemma 4 12B | Liquid LFM2.5-8B-A1B |
| --- | --- | --- |
| Weight file | 6,975,879,296 bytes | 5,155,564,768 bytes |
| Median elapsed per question, including withheld answers | 53.15 s | 31.83 s |
| Single observed process RSS, not peak or total unified memory | 8.28 GiB | 5.08 GiB |
| Drafts returned, not scientifically correct-answer counts | 7/8 | 6/8 |
| Requested numerical reference check | Called the tool | Did not call it, but described successful checks |
| Saved KEGG task | Read cached evidence; preserved identifiers; overextended a knockdown hypothesis | Did not read evidence; claimed the saved query/facts were unavailable |

Observed timings are not a controlled speed benchmark: desktop activity/cache state were not controlled and the candidate download overlapped part of the Gemma run. Gemma thinking was disabled; Liquid's required reasoning was enabled and consumed its generation budget. Upstream benchmark results cannot simply be transferred to these local quantizations and settings.

The serious Liquid failures outweighed its resource advantages. Gemma was retained, and Liquid's temporary weights/logs were removed. The comparison also exposed a hyphenated-number bypass in the numeric-prose checker; that gap was fixed **after** both model runs. The correction is documented separately and must not be presented as part of the frozen paired comparison.

## Why this does not prove Gemma is scientifically trustworthy

Gemma repeatedly overstated the role of FRET or proximity ligation in establishing direct binding, proposed directional knockdown hypotheses beyond membership-only evidence, and incorrectly suggested that using a likelihood ratio without a prior assumes a uniform prior. The actual saved statistic tests covariance under an independent-pixel Gaussian model, not binding versus non-binding. Both models had their new PLA answer withheld by application checks; a withheld answer is not a demonstrated scientific success.

A source identifier being valid does not establish that the attached claim is supported. A successful software test does not validate biological interpretation. A smaller model, lower temperature, longer answer or more confident explanation is not a scientific reliability guarantee. Gemma should explain supplied measurements and verified evidence with human review; it must not be used as an autonomous authority for binding, pathway activation or causal knockdown conclusions.

## Detailed, preserved records

- [Gemma evaluation: answers, observed failures, corrections and persistence check](docs/GEMMA_EVALUATION.md).
- [Paired Liquid/Gemma comparison: exact questions, answers, profiles, timings and manual review](docs/LIQUID_COMPARISON.md).
- [Evaluation history, including Qwen and Ministral](docs/ASSISTANT_EVALUATION.md).
- [Current model manifest, setup, privacy and safeguards](docs/LOCAL_ASSISTANT.md).
- Historical Qwen manifest: Git revision `c9f28c0`; historical Ministral manifest: `c63e4d6`; frozen paired-comparison implementation: `25644e0`; subsequent numeric-format fix: `d30e451`.

Gemma uses Apache-2.0. The assessed Liquid profile uses LFM Open License v1.0; its exact licence is retained alongside the other model notices. This record does not override model licences or the application's undecided source licence. Model weights are not committed to Git or bundled in the current installer.

## Requirements for a future replacement

Use the same versioned evaluation inputs and guards, add unseen cases, repeat stochastic runs, and review claims against actual source content and tool execution. Include expert-reviewed biological/statistical examples, missing and conflicting information, unsupported causal statements, metadata/unit errors, invalid identifiers and adversarial evidence. Score task completion separately from factual correctness and appropriate abstention. Validate memory/latency alongside representative stacks and native Windows execution. Retain a replacement only when evidence supports the decision; remove superseded managed weights after verification while preserving research data and small evaluation records.

## Future decision log

Append the date, exact profile/hash, evaluation revision, scientific/task failures, resource observations, limitations, decision and link to the complete evidence for every new assessment. Do not silently convert historical exploratory results into a controlled model ranking.


## Integration follow-up — 17 October 2026, source 0.1.11

Gemma remains the selected profile. A live, general Pearson-methodology question completed without an image, project save or online refresh (42.83 seconds reported by the agent loop, excluding model startup). The answer distinguished correlation from binding but overgeneralized the effect of channel brightness and described shared organelle localization imprecisely. This is another observed scientific limitation, not a correctness pass. The application now supplies a short method reference that explicitly covers affine invariance and other known statistical interpretation pitfalls. Historical Liquid/Qwen/Gemma comparisons retain their original prompts and results; no new paired model ranking is implied by the interface or prompt change.

The source 0.1.11 follow-up also exposed application-level issues. A recorded channel label containing a digit could be rejected as a generated measurement, and an overly broad tool note described null metrics as unperformed calculations. Both were corrected. Current summaries include completed-calculation status and recorded constant-channel facts. A targeted current-ROI retest then described undefined correlation and missing signal correctly without saving or internet access (57.65 seconds reported by the agent loop). A separate affine-invariance question was answered correctly with the method reference (29.31 seconds). These are targeted integration checks, not a fresh paired comparison, broad accuracy estimate or proof that Gemma is scientifically reliable.

## Added assessment — 17 October 2026, source 0.2.2

The [current candidate assessment](docs/MODEL_SELECTION.md) records the decision to keep Gemma if only one model is selected, the separate optional-vision proposal, the GPT-OSS-20B/120B comparison, and why Llama 3.2 Vision is a technically possible but unqualified replacement. No model change or download was made. The [manual](MANUAL.md#part-xi--local-assistant-and-model-decisions) explains the user-facing role.

Correction to earlier shorthand: **Gemma 4 12B supports multimodal inputs upstream; OrganelleScope currently uses it for text only.** The current GGUF/runtime image path has not been qualified. Evaluate enabling that path as well as Qwen2-VL before assuming a second model is required. GPT-OSS is a text challenger, not an image-input upgrade. MicroVQA results are external/historical and cannot rank our local Gemma profile against the proposed replacements.
