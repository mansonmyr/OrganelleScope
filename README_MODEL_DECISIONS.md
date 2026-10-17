# OrganelleScope: cumulative local-model decisions

This README is the accumulating decision record for the local assistant. Keep previous evaluations and their limitations when adding new candidates; append dated decisions rather than rewriting history into a claim that the current model is universally best. Gemma is currently retained as an **experimental, supervised interpreter**, not a validated biological reasoning engine. Measurements and statistical calculations remain in the deterministic application engine.

## Current decision — 17 October 2026

Retain **Gemma 4 12B Instruct, official Google QAT Q4_0**. Do not replace it with the assessed Liquid LFM2.5-8B-A1B Q4_K_M profile. Qwen3.5-4B and Ministral 3 8B remain retired. Only Gemma's weights are retained locally; small manifests, source history and evaluation records remain available. Retired models are not distributed.

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

- [Gemma evaluation: answers, observed failures, corrections and persistence check](README_MODEL_DECISIONS.md#preserved-assessment-gemma-evaluation).
- [Paired Liquid/Gemma comparison: exact questions, answers, profiles, timings and manual review](README_MODEL_DECISIONS.md#preserved-assessment-liquid-comparison).
- [Evaluation history, including Qwen and Ministral](README_MODEL_DECISIONS.md#preserved-assessment-assistant-evaluation).
- [Current model manifest, setup, privacy and safeguards](docs/LOCAL_ASSISTANT.md).
- Historical Qwen manifest: Git revision `c9f28c0`; historical Ministral manifest: `c63e4d6`; frozen paired-comparison implementation: `25644e0`; subsequent numeric-format fix: `d30e451`.

Gemma uses Apache-2.0. The assessed Liquid profile uses LFM Open License v1.0; its historical licence remains in Git history. This record does not override model licences or the repository/component licences. Model weights are not committed to Git or bundled in the current installer.

## Integration follow-up — 17 October 2026, source 0.1.11

Gemma remains the selected profile. A live, general Pearson-methodology question completed without an image, project save or online refresh (42.83 seconds reported by the agent loop, excluding model startup). The answer distinguished correlation from binding but overgeneralized the effect of channel brightness and described shared organelle localization imprecisely. This is another observed scientific limitation, not a correctness pass. The application now supplies a short method reference that explicitly covers affine invariance and other known statistical interpretation pitfalls. Historical Liquid/Qwen/Gemma comparisons retain their original prompts and results; no new paired model ranking is implied by the interface or prompt change.

The source 0.1.11 follow-up also exposed application-level issues. A recorded channel label containing a digit could be rejected as a generated measurement, and an overly broad tool note described null metrics as unperformed calculations. Both were corrected. Current summaries include completed-calculation status and recorded constant-channel facts. A targeted current-ROI retest then described undefined correlation and missing signal correctly without saving or internet access (57.65 seconds reported by the agent loop). A separate affine-invariance question was answered correctly with the method reference (29.31 seconds). These are targeted integration checks, not a fresh paired comparison, broad accuracy estimate or proof that Gemma is scientifically reliable.

## Added assessment — 17 October 2026, source 0.2.2

The [current candidate assessment](README_MODEL_DECISIONS.md#preserved-assessment-model-selection) records the decision to keep Gemma if only one model is selected, the separate optional-vision proposal, the GPT-OSS-20B/120B comparison, and why Llama 3.2 Vision is a technically possible but unqualified replacement. No model change or download was made. The [manual](MANUAL.md#part-xi--local-assistant-and-model-decisions) explains the user-facing role.

Correction to earlier shorthand: **Gemma 4 12B supports multimodal inputs upstream; OrganelleScope currently uses it for text only.** The current GGUF/runtime image path has not been qualified. Evaluate enabling that path as well as Qwen2-VL before assuming a second model is required. GPT-OSS is a text challenger, not an image-input upgrade. MicroVQA results are external/historical and cannot rank our local Gemma profile against the proposed replacements.


## Preserved assessment: Model Selection

The following sections preserve earlier assessments. Version-specific setup, licence retention and feature statements describe their historical builds; current operation is documented in the manual and current component notices. No new model ranking is implied by consolidating these records.

# OrganelleScope model selection and replacement rationale

Decision record · 17 October 2026 · source 0.2.2. This is a literature and integration assessment, not a new inference benchmark. No candidate weights were downloaded, and the active model was not replaced.

## Decision

Retain **Gemma 4 12B Instruct, official QAT Q4_0**, as the default local text assistant. This is an operational decision based on the working integration and its recorded local evaluations, not a claim of superior biomedical accuracy. Known qualitative errors remain in [Gemma evaluation](README_MODEL_DECISIONS.md#preserved-assessment-gemma-evaluation). The previous [Liquid comparison](README_MODEL_DECISIONS.md#preserved-assessment-liquid-comparison) and [assistant evaluation history](README_MODEL_DECISIONS.md#preserved-assessment-assistant-evaluation) remain part of the accumulated record.

If one model must be shipped, retain Gemma until a challenger passes the same application-specific evaluation. If optional vision becomes a priority, evaluate image support for this same Gemma checkpoint/runtime first, alongside Qwen2-VL-7B. Do not assume a second model is necessary simply because today's integration is text-only.

## Correcting the text-only distinction

Google's current [Gemma 4 12B model card](https://huggingface.co/google/gemma-4-12B-it) describes an encoder-free unified architecture accepting multimodal inputs. **The upstream model is not inherently text-only.** OrganelleScope currently sends metadata, native engine reports and evidence records as text; it does not send microscopy pixels, image patches or a rendered volume to the model. The pinned GGUF/runtime vision path has not been qualified here. Enabling images requires checking conversion contents, runtime support, image preprocessing, prompt formatting and actual local inference. Earlier documentation that says “text-only use” describes the application configuration, not the model family's theoretical capability.

The active file is `gemma-4-12b-it-qat-q4_0.gguf`, 6,975,879,296 bytes (6.98 decimal GB; about 6.50 GiB), SHA-256 `93567e57a8fe10b23569b9d9ec38cd005deedf71e29477c421a4b83f418a538b`. This file size is not peak unified memory. The application caps context at 8,192 tokens and runs a bounded read-only tool loop. See [local assistant configuration](docs/LOCAL_ASSISTANT.md).

## Gemma versus OpenAI GPT-OSS

| Consideration | Current Gemma configuration | GPT-OSS-20B | GPT-OSS-120B |
|---|---|---|---|
| OrganelleScope status | Integrated and locally assessed, with documented failures | Not installed or tested | Not installed or tested |
| Input in this app | Text plus engine/evidence records | Would be text only | Would be text only |
| Model structure | 12B named dense model | 21B total, 3.6B active parameters | Much larger alternative; outside the current laptop target |
| Local file size | Exact pinned file: 6.98 GB | Depends on selected distribution and precision; not measured here | Not measured here |
| Hardware evidence | Runs on the development M3/24 GB; full concurrent workload still needs qualification | Official Transformers guide describes approximately 16 GB VRAM with supported MXFP4 hardware; this is not an M3 memory guarantee | Official guide describes at least 60 GB VRAM or multi-GPU; exclude from the M3/24 GB target |
| Integration work | Existing checksum/runtime/prompt guards | Validate Harmony message and tool formatting, reasoning channels, quantization, cancellation and resource budgets | Same plus incompatible target memory budget |
| License | Upstream Apache-2.0; retain exact notices | Apache-2.0 plus applicable usage terms | Same |
| Recommendation | Keep default | Worth a later controlled text/tool-use trial | Do not target this deployment |

OpenAI documents [GPT-OSS-20B's architecture, tool capabilities and lack of image input](https://developers.openai.com/api/docs/models/gpt-oss-20b). Its active parameter count describes computation per token; the inactive experts still consume storage/memory. Fewer active parameters do not guarantee a smaller resident footprint than our Gemma file. The [Transformers guide](https://developers.openai.com/cookbook/articles/gpt-oss/run-transformers) gives hardware/precision-specific memory guidance, including a substantially larger BF16 footprint. Apple Silicon has a different memory/runtime path; measure it directly. The [Harmony specification](https://developers.openai.com/cookbook/articles/openai-harmony) is required integration knowledge; an API-compatible endpoint alone does not prove correct role, tool or reasoning handling. OpenAI also documents [local LM Studio operation](https://developers.openai.com/cookbook/articles/gpt-oss/run-locally-lmstudio).

GPT-OSS is a credible text reasoning/tool-use challenger. Published general benchmarks cannot establish whether it cites OrganelleScope evidence correctly, recognizes an undefined correlation, avoids causal pathway claims or behaves better with limited context. It would not add vision. There is no measured Gemma-versus-GPT-OSS latency, peak memory, accuracy or reliability result in this repository. No OpenAI API subscription/key is needed to run downloaded open weights locally; this is separate from hosted API services.

## Microscopy vision candidates and MicroVQA

The [MicroVQA paper](https://arxiv.org/html/2503.13399v1), Table 3, reports these overall multiple-choice accuracies in its published evaluation:

| Model | Overall | Expert visual understanding | Hypothesis generation | Experiment proposal |
|---|---:|---:|---:|---:|
| Qwen2-VL-7B | 48.8% | 54.1% | 43.3% | 49.6% |
| Pixtral-12B | 45.6% | 46.9% | 44.8% | 44.8% |
| LLaVA-Med-Mistral-7B | 43.0% | 37.3% | 47.1% | 41.6% |
| Llama-3.2-11B-Vision-Instruct | 30.3% | 32.4% | 29.3% | 28.7% |

These are historical benchmark results, not local four-bit evaluations or a comparison against Gemma 4. The paper notes output-format/instruction-following issues for Llama and special prompting/parsing for LLaVA-Med. Accuracy is not a probability that an arbitrary biological claim is correct. No model in this table has been qualified for our microscopy input pipeline.

**Qwen2-VL-7B:** a sensible vision comparator based on this particular benchmark. This is a different checkpoint and image-input task from the earlier Qwen3.5-4B text-assistant trial. A failure in that earlier configuration does not establish the performance of Qwen2-VL. See the [official checkpoint](https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct). It is not currently installed or offered by the app.

**Pixtral-12B:** a non-Qwen comparator. Its [official card](https://huggingface.co/mistralai/Pixtral-12B-2409) specifies a 12B decoder plus 400M vision encoder, variable image sizes, multiple-image examples and Apache-2.0. These are potentially useful for separate channel panels and selected Z slices; they do not prove organelle recognition accuracy. Its actual quantized/runtime footprint must be measured.

**Llama 3.2 Vision:** the [11B official card](https://huggingface.co/meta-llama/Llama-3.2-11B-Vision-Instruct) describes text/image input and text output under Meta's custom community license, with redistribution/attribution terms. The published microscopy result makes it a lower-priority candidate for this application, not a universally incapable model. The 90B variant is not appropriate for the current 24 GB target. Do not treat an 11B four-bit model as an 11 GB installation estimate or assume the full vision pipeline is compressed identically.

**LLaVA-Med:** scientifically relevant comparator, unsuitable as an unquestioned bundled default. The [v1.5 Mistral model card](https://huggingface.co/microsoft/llava-med-v1.5-mistral-7b) lists Apache-2.0 metadata but also restricts intended use to research/reproducibility and describes any deployed use, commercial or otherwise, as out of scope. Clarify redistribution/deployment expectations before product integration. Biomedical figure training is not validation on raw multichannel fluorescence stacks.

**BioVLM:** the [2026 prompt-learning project](https://arxiv.org/abs/2604.17629) found under this name evaluates cross-modality classification on MedMNIST+ 2D datasets. It is not a drop-in conversational generative assistant. The name is ambiguous; evaluate a different proposed BioVLM only after its exact repository/checkpoint is identified.

## Optional two-model architecture: considered, not implemented

A future user-initiated image question could supply labelled channel images, selected Z planes and ROI crops to a vision model. Its observations would be identified as model interpretations, then supplied alongside deterministic measurements and retrieved evidence to Gemma. Running one model at a time could limit peak resource competition, at the cost of model-switching latency. An optional separate download could avoid inflating the default installer. Keeping both weights would still consume disk space. This architecture remains a proposal; there is no image-question button or vision model download in the current build.

Do not feed a coloured composite without explaining its LUT, channel identities and contrast scaling. A 2D snapshot is not the entire calibrated 3D stack; crops/projections discard context. A VLM cannot recover information absent from the acquisition. Descriptive model observations must stay separate from numeric measurement, retrieved database claims and hypothetical mechanisms.

## Replacement evaluation protocol

Use one versioned corpus and the same engine records/evidence for every candidate. Freeze prompts, runtime, model hash, quantization, context length, generation settings and tool budget. Separate text-only questions from image questions. Include unknown/missing channels, blank/constant channels, channel-label swaps, LUT changes, anisotropic calibration, misleading composites, stale evidence and prompt-like text inside retrieved records. Compare:

1. Factual and methodological correctness, including likelihood versus posterior, proximity versus binding and pathway membership versus activation.
2. Tool selection/execution, exact identifier preservation and source-claim support, not merely citation syntax.
3. Appropriate abstention and correct treatment of missing documentation versus experiments not performed.
4. Visual description correctness, sensitivity to display choices and disagreement with expert annotations when images are used.
5. Repeated latency, total unified/VRAM footprint, concurrent 3D/image workload, cancellation, crash recovery, Windows/macOS parity and offline operation.

A candidate must improve the desired tasks without an unacceptable resource or error tradeoff. Until that result exists, keep the tested default and preserve the historical comparison. Download and delete model files only after an explicitly chosen trial and integrity checks; this documentation update does neither.



## Preserved assessment: Assistant Evaluation

# Preliminary local assistant evaluation

Development observations, **17 October 2026**, source milestone 0.1.9. This is a small engineering smoke test, not a biological benchmark, model ranking or a claim of validated interpretation.

## Current model: Gemma 4 12B (0.1.9)

The selected replacement is official Google Gemma 4 12B Instruct QAT Q4_0. See [the complete Gemma evaluation](README_MODEL_DECISIONS.md#preserved-assessment-gemma-evaluation) for real answers, observed failures, integration corrections and retests. This is an experimental interpreter, not a validated biological agent.

## Liquid comparison

A fresh paired diagnostic run retained Gemma and rejected Liquid as its replacement in this integration. See [the full Liquid/Gemma comparison](README_MODEL_DECISIONS.md#preserved-assessment-liquid-comparison) for eight cases per model, tool failures, observed timings, exact profiles and remaining scientific errors in both models. Draft-return counts are not accuracy scores.

## Historical model: Ministral 3 8B (0.1.8)

The previous model was official Mistral Ministral 3 8B Instruct Q4_K_M, 5,198,911,904 bytes, historical pinned revision and SHA-256 in Git revision c63e4d6. The complete downloaded file passed SHA-256 verification before installation. On Apple M3 / 24 GB, llama.cpp b11669 uses Metal, four CPU threads, one slot, an 8,192-token context and temperature 0.05. This is text-only evidence interpretation; no microscopy image or vision projector is passed to the model.

Three real local API requests used saved development projects with online access disabled:

| Request | Elapsed | Application tools | Observation |
| --- | --- | --- | --- |
| Interpret saved synthetic ROI results | 51.33 s | `inspect_project`, `read_measurements` | Distinguished intensity correlation from molecular binding; cited supplied measurements. Nine recorded quantities were returned separately by the application. |
| Run numerical references and assess publication readiness | 11.00 s | `inspect_project`, `run_reference_checks` | Explained that numerical agreement does not establish biological validity or publication readiness. |
| Repeat saved human TP53 KEGG query from cache | 27.80 s | `inspect_project`, `refresh_selected_evidence` | Used cached evidence and actual source IDs; distinguished pathway membership from activation and a causal silencing effect. |

The interface test completed in **42.03 seconds**. Its new Ministral answer and nine recorded quantities were saved with the earlier Qwen answer, then restored from project revision 4 after reloading; each answer retained its own model attribution. The model was unloaded after testing to release memory.

These are individual smoke-test timings, not a controlled comparison with Qwen or a biomedical reasoning benchmark. In the KEGG response the model also attributed a general methodological caution to “original KEGG documentation”; the retrieved membership record does not establish that attribution. Source-ID validation alone cannot verify citation entailment. This remains a limitation requiring human review and a curated evaluation corpus before a mature public release.

All 81 backend and 33 frontend tests passed, and the interface production build passed. Additional tests cover model-specific request settings, retained source IDs in bounded evidence payloads, conservative cleanup and runtime integrity receipts. Native Windows inference and installer bundling of the new model have not been qualified.

After the first successful new-model response, cleanup removed the superseded Qwen weights, the downloaded runtime archive and explicitly identified evaluation scratch files (2,719,767,635 bytes). Earlier cleanup removed obsolete build artifacts and the 0.1.2 installer (398,903,213 bytes): **3,118,670,848 bytes reclaimed in total**. The latest usable installer, active runtime, scientific images, saved projects, measurements, conversations and evidence were preserved. Re-running setup verified the installed model/runtime without downloading the removed archive again. The active 5.20 GB model is larger than the retired model; reclaimed space is not a claim of a net reduction in total installation size.

## Historical model: Qwen3.5-4B (0.1.7)

The following observations refer to the retired Qwen configuration; its weights have been removed. They do not measure Ministral performance. Model provenance remains in earlier Git history and saved response metadata.

### Historical configuration

Apple M3 / 24 GB unified memory; Qwen3.5-4B community Q4_K_M (historical size/hash/revision in Git revision c9f28c0); official llama.cpp b11669, Metal, four CPU threads, one slot, 8,192-token context, thinking disabled, temperature 0.2. No vision projector or raw microscopy image was passed to the model. The assistant used saved source metadata and deterministic reports from the existing synthetic validation stack (64×64, eight Z planes, two channels; XY spacing 0.1 µm, Z spacing 0.4 µm).

One exploratory process snapshot reported about **3.53 GiB RSS** for llama-server. This is not peak memory, a full accounting of Metal/unified allocations, or an installation requirement. Timings varied with prompt context, cache and rewrite checks; exploratory qualitative-answer tests took approximately **6–35 seconds** before the final structured rewrite check, and a cache-only KEGG test about **28 seconds**. The final cited ROI smoke test took **47.11 seconds**, including a format/grounding rewrite, and returned 9 recorded quantities separately from the model prose. The end-to-end interface check took **76.94 seconds** under concurrent desktop activity; its cited answer, measurement table and conversation survived saving and reopening. These are individual development observations, not a controlled latency benchmark. Native Windows execution, low-memory behavior and larger concurrent image workloads were not tested.

## Observations that changed the design

- An early free-text response used an unrecognised reference; it was withheld.
- More seriously, an early response misinterpreted a pixel-based ROI dimension as a physical distance despite reading the correct calibration. A source citation alone does not make generated arithmetic reliable.
- The application therefore presents recorded calibration/ROI quantities directly from saved engine fields, separately from generated qualitative prose. Matching source hash and image metadata are required for the displayed ROI quantity list.
- Generated prose is checked for numeric value patterns, supplied source IDs and URLs. Invalid drafts get one schema-constrained rewrite: qualitative text plus a citations array restricted to actual supplied source IDs. If that fails, the draft is withheld. The tested runtime did not consistently enforce all requested JSON fields during development, so explicit format instructions and application-side validation remain authoritative. This does not prove semantic correctness or prevent every spelled-out quantitative claim.

## Tasks exercised

| Task | Observed behavior / boundary |
| --- | --- |
| Inspect saved calibration and ROI results | Read the project/measurement tools and distinguished descriptive intensity correlation from molecular binding. Early unit error prompted the safeguards above; interpretation still requires review. |
| Does pixel spacing establish nanoscale optical resolution? | Distinguished sampling from optical resolution. No reconstruction/resolution claim was accepted as a measurement. |
| Run numerical references; assess publication readiness | Called the deterministic reference tool and explained that passing does not establish biological validity or publication readiness. |
| Repeat the exact saved human TP53 KEGG pathway query, cache only | Called `refresh_selected_evidence`, returned the cached membership/name sources and their hashes, cited supplied evidence IDs, and distinguished membership from measured activation or a proven silencing effect. No online permission was granted for this test. |
| Full application interaction | Saved and reopened the synthetic project; assistant runtime start/status and draft/reference handling were exercised through the interface. |

## Automated checks

The backend tests include project round trips/revisions, source integrity, calibration isolation, concurrent import-setting conflicts, recovery errors, session authentication, allowlisted tools and empty-argument schemas, history validation, tool budgets, offline query boundaries, fabricated reference/URL rejection, generated-number repair/rejection, single-system-message compatibility, model checksum rejection and recorded-quantity provenance. Frontend tests include restored validation/3D reports in React StrictMode, invalidation after changed settings, isolation from late callbacks on a closed project, and local assistant request permissions/response display.

## Required before a mature public release

Use a curated, versioned corpus with expected tool actions and source-supported claims, including positive/negative biological controls, ambiguous symbols, missing/stale/conflicting evidence, unseen experiments and adversarial provider content. Score citation entailment and claim correctness rather than merely checking whether a source ID exists. Evaluate hypothetical knockdown answers separately from measured comparisons. Measure repeated latency/peak memory, cancellation/recovery and coexistence with representative large stacks. Qualify native Windows and packaged offline installations. Passing this smoke test or the unit suite does not complete those gates.



## Preserved assessment: Gemma Evaluation

# Gemma 4 12B development evaluation — 17 October 2026

Source milestone 0.1.9. These are developer-reviewed smoke tests, not an independent biomedical benchmark or publication certification. Apple M3 / 24 GB; official Google QAT Q4_0 GGUF; pinned manifest in [LOCAL_ASSISTANT.md](docs/LOCAL_ASSISTANT.md); llama.cpp b11669, Metal, four CPU threads, context 8,192, temperature 1.0, top-p 0.95, top-k 64, thinking disabled, text only. Downloaded bytes passed the official SHA-256 check. No raw image or cloud LLM was used. Online evidence access was disabled; KEGG data came from the existing cache.

The integration also increases answer budgets and adds compact threshold/background context, so improvements cannot be attributed to the model alone. Sampling is not deterministic; one run per case does not estimate an accuracy rate. All outputs below passed the then-current application format checks; their semantic reviews show why that is insufficient.

## Initial six cases

### roi-controls

Question: Inspect the saved ROI results and explain what controls would be needed before claiming molecular binding. Cite the supplied sources.

Elapsed: 95.32 s. Tool record: inspect_project, read_measurements.

Observed answer:

> The saved measurements for the synthetic region show high correlation coefficients and strong intensity associations between the two channels. However, these results are purely descriptive and represent native source intensities within a single ROI. Because conventional microscopy cannot establish molecular binding or causality from colocalization, these findings do not support such a claim. The current analysis lacks spatially calibrated significance, independent experimental replicates, and biological validation, which are necessary to distinguish consistent signals from noise. Additionally, the use of zero thresholds and a lack of background correction require further sensitivity checks before interpreting the overlap accurately. To move toward a valid biological conclusion, one would need to incorporate independent microscopy-software benchmarks, biological replicates, and specificity controls. These next steps would help establish whether the observed spatial association is a result of specific molecular interactions or non-specific signal distribution. [measurements] [project]

Review: Partial improvement: notices zero thresholds/background and distinguishes description from binding. Control suggestions remain broad; independent software agreement is not evidence of molecular interaction. The prompt/context and answer budgets changed, so this is not a controlled model comparison.

### threshold-trap

Question: The saved Manders coefficients show complete overlap. Can I conclude the proteins bind? Inspect the saved threshold and background settings, explain their implications, and suggest practical next checks with their purpose.

Elapsed: 52.13 s. Tool record: inspect_project.

Observed answer:

> The recorded measurements indicate a high degree of spatial overlap, but this does not establish protein binding. Colocalization is limited by optical resolution and does not prove molecular interaction or causality. The current analysis uses a zero threshold for all channels and lacks background correction, which means the overlap may be influenced by noise or non-specific signal rather than specific localization. Because of these settings, the results lack the necessary specificity to confirm biological interaction. To validate these findings, it is advised to apply specific intensity thresholds to isolate target structures and perform background subtraction to improve signal clarity. Additionally, conducting a sensitivity analysis by varying thresholds and using a known non-interacting protein as a negative control would help determine if the observed overlap is biologically significant or an artifact of the current imaging parameters. [project]

Review: Partial: sensible setting cautions, but the model did not request the actual measurement report and accepted the user-supplied overlap premise. This motivated automatic provision of a saved-measurement summary before generation; a targeted retest follows.

### missing-controls

Question: Does this project prove I never performed negative controls or knockdown experiments? Explain exactly what is known and unknown. Is synthetic data inherently scientifically invalid?

Elapsed: 30.45 s. Tool record: inspect_project.

Observed answer:

> The absence of documented negative controls or knockdown experiments in the saved project context is not proof that they were not performed. The current project documentation only reflects the specific state and parameters of the data currently loaded and saved in the workspace.

> The available project data [project] provides the image dimensions, calibration, and analysis settings for a synthetic validation file. It shows the current workspace configuration, including a circular region of interest and specific thresholding settings. It does not contain a comprehensive log of all experiments conducted or a full experimental design history.

> Information regarding whether any other samples, such as controls or knockdown lines, were processed in separate sessions or different files is unknown from the current project state. The system does not record actions taken outside of the saved metadata.

> Synthetic data is used here for validating numerical behavior and software functionality. While it can confirm that the analysis tools are calculating values correctly, it does not establish biological validity. Synthetic data is a methodological tool for troubleshooting and verification, not a substitute for empirical biological evidence.

> Practical next checks should include reviewing the full experimental repository to identify related files containing control datasets. You may also wish to document the specific reasons for using synthetic data to clarify its role in your validation workflow.

Review: Acceptable on this case: distinguishes undocumented controls from controls never performed, and treats synthetic data as useful for numerical validation. No independent biological validation was demonstrated.

### references

Question: Run the numerical reference checks. Explain whether passing makes this analysis publication-ready. Cite supplied sources.

Elapsed: 33.87 s. Tool record: inspect_project, run_reference_checks.

Observed answer:

> The numerical reference checks were completed, and all cases passed with zero or negligible absolute errors [reference]. This confirms that the analysis engine is calculating correlation coefficients and analytic thresholds in a manner consistent with standard libraries like SciPy and hand-derived examples.

> Passing these checks does not make the analysis publication-ready. These checks only validate the deterministic numerical behavior of the software's algorithms against known synthetic values. They do not certify the biological validity of the data, the quality of the image acquisition, or the significance of the observed correlations.

> To move toward publication, you must perform independent biological validations. This includes ensuring that the synthetic data used for these checks reflects your actual experimental conditions. Furthermore, the current Fiji benchmark status is listed as pending, indicating that external software cross-validation is also required.

> Practical next steps involve verifying your specific experimental controls and performing independent statistical assessments. You should also confirm that the image acquisition parameters and processing steps (such as background subtraction and thresholding) are appropriately optimized for your biological targets.

Review: Partial: called numerical checks and correctly rejected publication certification. The advice about synthetic data reflecting experimental conditions is broad; numerical unit references and realistic image simulations serve different purposes.

### kegg

Question: Repeat the exact saved KEGG query using only cached evidence. Does TP53 pathway membership establish activation or a causal effect of silencing? Distinguish retrieved facts, your methodological advice, and hypotheses. Cite only what supplied records actually support.

Elapsed: 117.64 s. Tool record: inspect_project, inspect_project, read_evidence.

Observed answer:

> The KEGG query confirms that hsa:T157 is associated with the p53 signaling pathway and various other functional networks including apoptosis and cell cycle pathways. This membership identifies potential functional roles but does not measure pathway activation or provide evidence of a causal effect resulting from silencing. Because KEGG records represent static database associations, they cannot establish whether a pathway is currently active or how it responds to specific perturbations. To determine these factors, experimental measurements such as knockdown assays or reporter assays are necessary. Methodologically, these results should be used as a framework for generating hypotheses rather than as proof of biological mechanism. Future steps should include experimental validation to distinguish between predicted functional associations and actual cellular responses. [evidence-1-1]

Review: Failed identifier fidelity: generated hsa:T157 instead of the retrieved hsa:7157. The original numeric-prose filter treated the numeric component of a real KEGG identifier as a generated quantity, and the rewrite could evade it by changing the identifier. Exact supplied human KEGG gene IDs are now exempted from the numeric filter; altered/unknown IDs are rejected. This does not validate arbitrary gene symbols or citation entailment.

### missing-image

Question: What do my microscopy images show about centrosome and mitochondrial colocalization? Report what the saved project actually establishes; do not assume any images or measurements exist.

Elapsed: 55.91 s. Tool record: inspect_project, inspect_project, read_measurements.

Observed answer:

> The current project does not contain any images or saved measurements related to centrosome and mitochondrial colocalization. The inspection of the saved project shows that no ROI, spatial, or sensitivity data have been recorded. Because no data is available in the project, it is not possible to establish any findings regarding the spatial relationship between these organelles. The absence of saved results does not prove that experiments were not performed, but rather indicates that no data has been finalized in the current session. To proceed, image acquisition and region of interest definitions for both the centrosome and mitochondria are required. Subsequently, running a colocalization or spatial proximity analysis is necessary to generate the data needed for interpretation. It is important to note that conventional microscopy cannot establish molecular binding or causality from colocalization alone. [project] [measurements]

Review: Mostly appropriate: found the evidence-only project had no saved image/measurements and did not invent organelle colocalization. The phrase "no data has been finalized" is broader than the actual finding that no such data is saved in this project.

## Integration corrections and retests

After these cases, every saved ROI report supplies a bounded summary of settings and metrics in the initial context, with a visible application tool record. Human KEGG gene identifiers are collected from actual evidence tool records: exact identifiers are permitted in otherwise qualitative prose and altered identifiers are rejected. Unit tests cover both correct and incorrect identifiers and numeric claims alongside them. This is a narrow exact-copy check, not a universal biological entity validator or semantic proof.

### Retest: threshold-trap

Elapsed: 64.69 s. Tool record: inspect_project, read_measurements.

> The saved results do not provide evidence of protein binding. High correlation coefficients indicate spatial overlap of signals but cannot establish molecular interaction or causality. Because the analysis utilized a zero threshold and no background correction, the results may include noise or non-specific signals, which can inflate overlap scores. These settings necessitate sensitivity checks before any qualitative interpretation of the data can be made. The results are currently categorized as engineering-tested and lack the biological controls, replicates, or biochemical assays required for publication readiness. To advance the analysis, you should perform signal-to-noise ratio assessments and apply specific thresholds to confirm if the overlap is restricted to high-confidence signals. Furthermore, experiments such as proximity ligation assays are required to distinguish between shared localization and direct binding. [measurements] [project]

Review: the automatic summary now makes actual saved settings/metrics available even without a model-selected report request. Identifier/citation/numeric format checks pass. Scientific interpretation remains **partial**: the answer calls proximity ligation assays "required" to distinguish direct binding. PLA measures probe proximity and is not a universal requirement or, by itself, proof of direct binding. The [manufacturer describes its proximity mechanism](https://www.sigmaaldrich.com/VG/en/products/protein-biology/duolink-proximity-ligation-assay); the [original method](https://www.nature.com/articles/nmeth947) studies complexes in situ. This is an example of a qualitative overclaim that the format checks do not reject. Also, "before any qualitative interpretation" is too absolute; the settings limit biological interpretation but do not erase descriptive observations.

### Retest: kegg

Elapsed: 53.31 s. Tool record: inspect_project, read_evidence.

> The cached KEGG query for hsa:7157 identifies its membership in several pathways, including the p53 signaling pathway (hsa04115) [evidence-1-1].

> KEGG pathway membership does not establish pathway activation or a causal effect of silencing. This data represents a static functional classification of a gene's potential involvement in a biological process.

> Methodologically, pathway membership serves as contextual evidence for potential interactions but requires experimental validation to determine if a pathway is active or if a specific gene is functionally silenced.

> Hypothetically, if hsa:7157 is silenced, it could impact the downstream signaling of the p53 pathway, but this is a predicted outcome based on the database record, not a measured result from your project.

Review: the exact retrieved identifier hsa:7157 and pathway hsa04115 are preserved; activation and causality are not presented as measured. The silencing sentence is labelled hypothetical, but calling it a "predicted outcome based on the database record" still overstates a membership-only record: the record alone does not provide a directional perturbation model. No mechanistic knockdown prediction has been validated.



## Interface persistence check

A final interface request used the prior Qwen/Ministral conversation history. Gemma completed in 50.21 seconds, identified zero thresholds/no background correction, distinguished undocumented controls from experiments never performed, and displayed nine engine-derived quantities separately. The conversation was saved and restored from project revision 5, with each older answer retaining its own model attribution. The model was unloaded after testing. The advice remains broad; background correction cannot by itself guarantee specific signal, and the appropriate orthogonal validation depends on the biological question.

## Cleanup and checks

The superseded Ministral weights (5,198,911,904 bytes) were removed after successful verified Gemma inference. Repeat setup verified the existing model/runtime without downloading a runtime archive again. Only the active 6.98 GB model is retained; the active runtime and small licence/history records remain. Images, scientific evidence, saved projects and earlier conversations are preserved. Backend: 86 tests passed; frontend: 33 tests passed; UI production build passed. These are application checks, not a biomedical accuracy score. No new installer is published in this milestone.

## Remaining release gates

Real biological controls and independent experiment/cell labels, citation-entailment scoring, systematic repeat runs, adversarial/conflicting evidence, larger stacks sharing memory with the model, cancellation/recovery, and native Windows/offline installer qualification remain outstanding. The interpretation remains an experimental draft. Preserve source measurements as the authority; do not treat model confidence or longer answers as validation.


## Source 0.2.4 interpretation context assessment

The selected model is unchanged. [The current review](README_MODEL_DECISIONS.md#preserved-assessment-assistant-interpretation-review) records synthetic constant-channel, mask-proximity, KEGG/knockdown and likelihood/Bayes scenarios, including a timeout and a separate follow-up. Report-aware context and deterministic application notes improve the information available to the assistant; no improvement is attributed solely to model weights, and these few developer-reviewed drafts do not establish biomedical accuracy.



## Preserved assessment: Liquid Comparison

# Liquid versus Gemma — local application comparison

17 October 2026. **Decision: retain Gemma; do not select Liquid as the replacement in this integration.** Liquid reduced storage and observed resource use, but produced serious scientific and tool-use errors. Gemma also remains scientifically unreliable for autonomous conclusions. This is a small developer-reviewed diagnostic comparison, not a blinded biomedical benchmark, an accuracy-rate estimate or a judgement of every model in either family.

## Conditions and limitations

Apple M3 / 24 GB; same llama.cpp b11669 runtime, Metal, four CPU threads, one model at a time, 8,192-token context. Same eight questions, source projects/revisions, empty conversation history, application system prompt, tool allowlist and pre-existing reference/identifier/numeric checks. Actual recorded quantity lists were checked equal wherever both models returned answers. No project writes, pixel-data transmission or online evidence access; KEGG operations were cache-only. Six questions repeat earlier cases and two are new probes. No prompt changes were made between these two runs.

Gemma uses its existing official QAT Q4_0 profile (temperature 1.0, top-p 0.95, top-k 64, thinking disabled). Liquid uses the official Q4_K_M profile (temperature 0.2, top-p 0.95, top-k 80, repetition penalty 1.05, required reasoning enabled). Both use the same 1,600-token generation / 1,200-token rewrite caps; Liquid's reasoning consumes part of its generation allowance. These are practical profile comparisons, not identical inference conditions or full-precision vendor benchmarks. A token-budget or parser issue cannot be inferred solely from a generic withheld-answer error. No internal reasoning is saved in this report.

Each case was run once without a fixed seed. Desktop activity, cache state, and the Liquid download overlapping the Gemma run were not controlled. Reported times include tools/rewrites and are observations, not a controlled speedup claim. RSS samples were taken during different points of generation and exclude a complete accounting of Metal/unified allocations; they are not peak memory or minimum RAM requirements.

## Operational observations

| Observation | Gemma 4 12B | Liquid LFM2.5-8B-A1B |
| --- | --- | --- |
| Exact model bytes | 6975879296 | 5155564768 |
| Startup incl. integrity check (s) | 4.35 | 3.57 |
| Median elapsed per case incl. withheld answers (s) | 53.15 | 31.83 |
| Elapsed range across cases (s) | 20.84–68.02 | 20.61–54.43 |
| Accepted drafts returned (not correct-answer count) | 7/8 | 6/8 |
| Single observed process RSS (GiB) | 8.28 | 5.08 |

A response passing application format checks can still be scientifically wrong. Neither draft-return count nor software-test count is an interpretation accuracy score.

## Scientific and task review

| Case | Gemma | Liquid |
| --- | --- | --- |
| roi-controls | Partial: useful settings/missing-controls discussion, but treats co-IP or FRET as necessary validation; methods should be matched to the claim, and complex association/proximity should not be equated with direct binding. | Withheld by the response guard after its rewrite; no accepted scientific answer. The generic error does not distinguish a numeric, identifier or reference failure. |
| threshold-trap | Scientifically problematic: recommends FRET/PLA for "definitive proof of binding". Good threshold/background cautions do not correct that overclaim. | Incorrect processing claim: calls the radius setting an applied line filter, although background is none and sigma is zero. Also treats undocumented controls as absent and calls any positive signal significant. A hyphenated numeric unit evaded the then-current numeric-prose check. |
| missing-controls | Appropriate core distinction between undocumented and never performed; acknowledges synthetic validation. Its blanket publication wording should be read only in the context of the present biological claim. | Appropriate core distinction when explicitly asked; recognizes the role of synthetic validation. This contrasts with its unsupported absence assertions in other answers. |
| references | Requested and executed run_reference_checks, accurately reported passing numerical checks and separated them from biological validation. The proposed publication requirements remain broad. | Did not call run_reference_checks, despite being asked. Described successful checks and a "zero-background line analysis" without that tool result. A previously saved engineering status is not proof a new reference run occurred. |
| kegg | Read cached evidence and preserved identifiers. However, it suggested downregulation on silencing based on pathway membership; the membership record does not support a directional causal prediction, even when labelled hypothetical. | Did not read or refresh saved evidence. Claimed the saved query/cache facts were unavailable even though the same cached project and tools were supplied. This is a task/tool-use failure, not evidence of an empty cache. |
| missing-image | Correctly recognized the evidence-only project had no saved microscopy image/measurement and did not invent a colocalization finding. | Correctly declined a colocalization conclusion, but fabricated that the project recorded images having been analyzed; the supplied project image is null and core settings are empty. |
| unseen-pla | Withheld by the response guard; no accepted answer, so this is not a demonstrated scientific success. | Withheld by the response guard; no accepted answer, so this is not a demonstrated scientific success. |
| unseen-bayes | Partially correct refusal to infer binding probability, but incorrectly says using a likelihood ratio without a prior assumes a uniform prior. A descriptive frequentist statistic does not silently acquire a prior, and the saved covariance test is not a binding likelihood model. | Correctly says a prior/model is needed, but misidentifies the statistic as having a no-binding null. The actual saved method compares zero versus unrestricted covariance, not binding versus non-binding. A prior alone cannot repair that mismatch. |

Review references: the saved [ROI methods](MANUAL.md#part-vi--roi-measurements-and-channel-associations) define the Gaussian covariance statistic and explicitly exclude binding-probability interpretation. [Duolink's mechanism](https://www.sigmaaldrich.com/VG/en/products/protein-biology/duolink-proximity-ligation-assay) measures probe proximity; direct binding does not logically follow from that observation alone. The introduction of the [primary ReLo study](https://pmc.ncbi.nlm.nih.gov/articles/PMC10991417/) distinguishes candidate associations identified by approaches such as co-IP from subsequent direct-binding validation. These sources informed the developer review; they were not supplied as new tool evidence during either model run.

## Exact profiles

### Gemma 4 12B Instruct QAT Q4_0

- upstream: https://huggingface.co/google/gemma-4-12B-it
- quantization: https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf
- revision: 29d097773436b69ff9feafd636ab4cf873786537
- filename: gemma-4-12b-it-qat-q4_0.gguf
- bytes: 6975879296
- sha256: 93567e57a8fe10b23569b9d9ec38cd005deedf71e29477c421a4b83f418a538b
- license: Apache-2.0
### Liquid LFM2.5-8B-A1B Q4_K_M

- upstream: https://huggingface.co/LiquidAI/LFM2.5-8B-A1B
- quantization: https://huggingface.co/LiquidAI/LFM2.5-8B-A1B-GGUF
- revision: 49c14831707011e64d70b2ebd8462ba08d608434
- filename: LFM2.5-8B-A1B-Q4_K_M.gguf
- bytes: 5155564768
- sha256: 4923ec14f06b968b74d663e5949867d2d9c3bf13a20b8be1a9f9af39989b2bb0
- license: LFM-Open-License-1.0

Liquid's licence is LFM Open License v1.0, not Apache-2.0; the exact upstream licence is retained in third_party/Liquid-LFM-LICENSE.txt. Neither candidate weights nor runtime binaries are committed or bundled in an installer by this assessment.

## Observed answers

### roi-controls

Question: Inspect the saved ROI results and explain what controls would be needed before claiming molecular binding. Cite the supplied sources.

**Gemma — 65.67 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The current analysis shows a strong linear and monotonic relationship between the signals of the two channels within the specified circular ROI. However, these results do not provide evidence for molecular binding because conventional microscopy and colocalization analysis cannot establish causality or specific binding events. The results are descriptive and lack calibrated p-values or spatial dependence modeling.

> To establish molecular binding, several controls are needed. This includes independent experimental replicates and biological controls to ensure the observed correlation is not an artifact. Furthermore, biochemical assays like Co-Immunoprecipitation or FRET are necessary to validate physical proximity, as colocalization alone is insufficient for such claims.

> Methodological next steps include performing sensitivity checks by testing various threshold levels and applying background subtraction, as the current zero threshold and lack of background correction may impact the interpretation. The absence of these controls in the current record does not prove they were not performed independently. [project] [measurements]

**Liquid — 30.36 s**

Withheld/error: The assistant returned an unverified reference, altered identifier or a generated quantitative claim. Its answer was withheld; try a narrower question.

### threshold-trap

Question: The saved Manders coefficients show complete overlap. Can I conclude the proteins bind? Inspect the saved threshold and background settings, explain their implications, and suggest practical next checks with their purpose.

**Gemma — 49.77 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The saved measurements do not allow for a conclusion regarding protein binding. The high correlation observed is a descriptive statistic of pixel intensity overlap in synthetic data and does not establish molecular interaction or causality. Conventional microscopy cannot determine binding from colocalization alone.

> The analysis utilized zero thresholds and no background correction [measurements]. This configuration means that even low-intensity noise may contribute to the overlap statistics, potentially inflating the correlation. Without background subtraction or refined thresholding, the sensitivity to noise remains a primary limitation.

> To improve the validity of these results, it is advised to implement background correction and define specific intensity thresholds to isolate relevant signals. Furthermore, because biological controls are currently undocumented, establishing a baseline with a known non-interacting protein pair is necessary. For definitive proof of binding, functional assays such as FRET or proximity ligation should be performed to distinguish physical interaction from shared localization. [measurements]

**Liquid — 54.43 s**

Tool record: inspect_project (application context), read_measurements (application summary context), inspect_project (model request).

> The recorded settings used a zero‑threshold mode with no background correction, applying a 20‑pixel radius line filter; this approach treats any signal above zero as significant, which amplifies low‑level noise and does not guarantee true co‑localization. Consequently, the observed complete overlap of Manders coefficients reflects spatial similarity rather than direct protein interaction. Because no biological controls or independent replicates are present, the data do not provide definitive evidence of binding. To assess physical association, repeat the analysis with background subtraction, include a negative control ROI, and obtain additional biological samples for replication. [project] [measurements]

### missing-controls

Question: Does this project prove I never performed negative controls or knockdown experiments? Explain exactly what is known and unknown. Is synthetic data inherently scientifically invalid?

**Gemma — 25.57 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The absence of negative controls or knockdown experiments from the saved records is not proof that they were not performed. The current project state only reflects the data explicitly saved to the application; it does not account for any external experiments, datasets, or procedures that were not imported or recorded here.

> The measurements in this project are restricted to descriptive statistics for synthetic data. Specifically, the project contains a Pearson correlation and a Spearman correlation for the synthetic-region [measurements]. These values characterize the relationship between two channels in a synthetic image but do not establish biological causality, molecular binding, or the effects of any genetic manipulations.

> The results are currently labeled as engineering-tested but biologically unvalidated [measurements]. Because the data is synthetic, it serves to verify that the software and analysis pipeline are functioning as expected. Synthetic data is not inherently scientifically invalid for engineering and software validation purposes, but it cannot be used to establish biological truths or publication-ready results.

> To move toward a scientifically valid conclusion, you would need to perform independent experimental replicates and include biological controls. Practical next steps should include recording these experimental results and performing a comparison between control and treatment groups to assess the significance of any observed phenotypes.

**Liquid — 31.3 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The saved project provides no evidence that negative controls or knockdown experiments were ever carried out, so it cannot be used to prove they were never performed. [project]

> What is documented: the analysis employed a synthetic ROI with a zero background threshold and no background correction; there are no biological controls established (as noted in the project's controls note). [measurements]

> The absence of any mention of such experiments means that their existence or absence remains unknown. No additional documentation about negative controls or knockdown assays is present.

> Synthetic data generated by this pipeline is not inherently scientifically invalid; it can validate numerical behavior, but biological relevance requires independent experimental verification. Therefore the project alone does not establish whether such controls were used. [project][measurements]

### references

Question: Run the numerical reference checks. Explain whether passing makes this analysis publication-ready. Cite supplied sources.

**Gemma — 20.84 s**

Tool record: inspect_project (application context), read_measurements (application summary context), run_reference_checks (model request).

> The numerical reference checks were successfully performed and passed [reference]. These results confirm that the calculation engine is producing expected values for Pearson correlation, Spearman correlation, and thresholded metrics compared to standard reference libraries.

> Passing these checks does not make the analysis publication-ready. The results represent an engineering validation of the software's mathematical consistency rather than a certification of biological validity. The current project status explicitly notes that biological validation is pending and the results are not publication-ready [measurements].

> To move toward publication, you must provide independent experimental replicates, establish biological controls, and perform a spatially calibrated significance analysis. These steps are required to distinguish these synthetic measurements from real biological interactions [measurements].

**Liquid — 32.36 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The saved results demonstrate that the numerical processing pipeline performs correctly according to its internal validation, as confirmed by the zero‑background line analysis and pairwise channel comparison (see [project] and [measurements]). However, the report explicitly states that biological controls and independent experimental replicates are absent, and it notes that spatially calibrated significance and experiment‑level inference have not been established. Therefore, despite successful numerical checks, the analysis does not meet the criteria for publication readiness. The limitations include lack of validation in real biological contexts and reliance on synthetic data for quantitative behavior; a separate experimental study is required to confirm observed interactions. Next steps should involve independent microscopy or biochemical assays to verify the findings under native conditions. [project] [measurements]

### kegg

Question: Repeat the exact saved KEGG query using only cached evidence. Does TP53 pathway membership establish activation or a causal effect of silencing? Distinguish retrieved facts, your methodological advice, and hypotheses. Cite only what supplied records actually support.

**Gemma — 68.02 s**

Tool record: inspect_project (application context), read_evidence (model request).

> The retrieved records confirm that hsa:7157 is associated with the p53 signaling pathway (hsa04115) in Homo sapiens [evidence-1-1]. This membership is based on functional mapping within the KEGG database.

> KEGG pathway membership does not establish pathway activation or a causal effect of silencing. Database records indicate that a protein is a component of a biological pathway, but they do not provide information on the current activity state of that pathway or the functional consequences of protein manipulation in a specific experimental context.

> As methodological advice, you should distinguish between this general database association and your specific experimental results. To establish activation or causal effects of silencing, you would need to perform functional assays, such as measuring downstream signaling markers or performing a knockdown experiment followed by phenotypic analysis.

> A hypothesis for further research could be that silencing hsa:7157 leads to the downregulation of pathways associated with apoptosis or cell cycle regulation, given its reported membership in those pathways [evidence-1-1]. However, this remains an inference and is not supported by the current measurement data.

**Liquid — 20.89 s**

Tool record: inspect_project (application context).

> Unable to repeat the saved KEGG query because it was not provided; therefore no conclusion about TP53 pathway activation or a causal effect of silencing can be drawn from the cached data. No retrieved facts are available in the current evidence cache.

> Methodological advice: establishing causality requires experimental perturbation rather than observational association.

> Hypotheses: (1) the saved KEGG results may reflect only correlation and do not establish activation or a causal effect of TP53 silencing; (2) any observed relationship remains untested without additional functional assays. [project]

### missing-image

Question: What do my microscopy images show about centrosome and mitochondrial colocalization? Report what the saved project actually establishes; do not assume any images or measurements exist.

**Gemma — 56.53 s**

Tool record: inspect_project (application context), inspect_project (model request), read_measurements (model request).

> The saved project currently lacks any microscopy images, ROI measurements, or spatial data regarding the colocalization of centrosomes and mitochondria. Therefore, no biological findings or spatial relationships can be established from the available data. The absence of these records in the project does not confirm that the experiments were not conducted, but rather that no results have been saved to the current session. To perform this analysis, you would need to define regions of interest for both organelles and run a colocalization measurement. Once data is available, it is important to review the threshold and background correction settings to ensure sensitivity. Qualitative assessment of the overlap will then provide information on their spatial relationship. This is a methodological step to establish potential proximity, but it does not demonstrate molecular binding or causality. [project] [measurements]

**Liquid — 20.61 s**

Tool record: inspect_project (application context), inspect_project (model request).

> The saved project contains only a note and no ROI or measurement data, so it does not establish any centrosome‑mitochondria colocalization (see [project]). It records that the images were analyzed but provides no quantitative overlap information. No statistical test results or colocalization metrics are present. Consequently, the project establishes nothing about spatial association between these organelles. [project]

### unseen-pla

Question: A colleague reports a positive proximity ligation signal for these proteins and wants to report direct binding. What can the saved project and that reported result establish? What remains unknown? Distinguish the reported scenario from saved measurements.

**Gemma — 63.02 s**

Withheld/error: The assistant returned an unverified reference, altered identifier or a generated quantitative claim. Its answer was withheld; try a narrower question.

**Liquid — 47.06 s**

Withheld/error: The assistant returned an unverified reference, altered identifier or a generated quantitative claim. Its answer was withheld; try a narrower question.

### unseen-bayes

Question: Can the Gaussian likelihood-ratio statistic in the saved ROI report be converted into a posterior probability of protein binding using Bayes theorem without specifying a prior? Explain the assumptions and missing information. Do not calculate a value.

**Gemma — 33.46 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The Gaussian likelihood ratio statistic provided in the measurements is a descriptive value and cannot be converted into a posterior probability of protein binding without a specified prior. Bayes theorem requires the combination of a likelihood (which the current statistic relates to) and a prior probability to derive a posterior probability.

> The current measurements are based on a synthetic dataset and lack the biological priors necessary for such an inference. Using a likelihood ratio without a prior assumes a uniform prior, which may not accurately reflect the biological likelihood of protein interaction in a specific cellular context.

> The measurements do not account for spatial dependence or experimental controls, which are necessary to establish a meaningful likelihood of binding. The report explicitly notes that the statistic is a descriptive Gaussian likelihood ratio and does not provide a calibrated probability or model spatial dependencies.

> Because the project uses a zero threshold and no background correction, the sensitivity of the results is not established. Furthermore, conventional microscopy cannot establish molecular binding or causality from colocalization alone, making any derived probability a hypothesis rather than a measured finding.

> To proceed, you would need to define a biologically relevant prior based on existing literature or experimental replicates. You would also need to perform sensitivity checks on the ROI thresholds and background settings to ensure the underlying data supports the intended interpretation.

> Source IDs: [measurements]

**Liquid — 34.66 s**

Tool record: inspect_project (application context), read_measurements (application summary context).

> The Gaussian likelihood‑ratio statistic reported in the ROI summary cannot be directly transformed into a posterior probability of protein binding without first specifying a prior distribution, because Bayes’ theorem requires both the likelihood and an explicit prior to yield a posterior. The analysis assumes that the LR reflects a test statistic under a null hypothesis of no binding, with independent measurements and that the Gaussian model accurately describes the data; however, these assumptions are not validated in the saved report. Missing information includes the chosen prior for binding probability, calibration or reference distributions needed to convert the LR, details on experimental replicates or multiple‑testing corrections, and confirmation that the statistic has been normalized as a likelihood ratio rather than a raw test output. Consequently, any inference about binding would be speculative without these elements [project][measurements] [project] [measurements]

## Reproducing the development comparison

The runner requires the named saved synthetic validation project and cached-KEGG development project. It does not create biological fixtures or mutate projects. Review those local inputs and the case expectations before substituting data. Use scripts/setup-local-assistant.py --candidate liquid --download for an explicit verified candidate download; this does not change the application model. Run scripts/evaluate-local-assistant.py with --model gemma or --model liquid and a local --output path, sequentially. Review final answers against their tool records; the runner does not award semantic pass scores.

## Decision and next work

Keep Gemma as the selected experimental model and remove Liquid's evaluation weights after completing this review. Preserve the compact results, profiles, licence and runner for reproducibility. No replacement installer is published. Prioritize claim-level evidence support, a curated microscopy-methods knowledge source, explicit checks that requested actions actually ran, and an expert-reviewed biological/statistical evaluation set before considering any local model a trustworthy scientific interpreter.

## Cleanup and application checks

After both owned evaluation processes stopped, the verified Liquid candidate weights were removed, reclaiming 5,155,564,768 bytes. Evaluation runtime logs were removed; the current Gemma weights/runtime, images, projects, measurements, conversations and evidence were preserved. The application model remains Gemma. All 88 backend tests passed for the comparison/profile support. No frontend implementation changed in this assessment.

## Post-comparison numeric-format correction

The paired evaluation corresponds to Git revision 25644e0, before this correction; no model prompt/guard was changed between the two runs. The subsequent application patch normalizes full-width digits and ASCII/Unicode dash variants before checking generated numeric quantities. Four hyphenated-unit regression cases are rejected while protein identifiers such as TP53/53BP1, 3D notation and exact supplied hsa:7157 remain permitted. Rechecking Liquid's previously accepted threshold answer now rejects it. All 93 backend tests pass after the fix. This closes that formatting gap; it does not verify semantic correctness, cover every spelled-out quantitative statement or repair the model's fabricated processing claim. The two complete eight-case model runs were not repeated after this targeted guard correction.



## Preserved assessment: Assistant Interpretation Review

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

Records: [initial run](docs/validation/ASSISTANT_INTERPRETATION_BENCHMARK.json), [separate follow-up](docs/validation/ASSISTANT_INTERPRETATION_FOLLOWUP.json), [synthetic harness](scripts/validation/evaluate_interpretation.py). The harness refuses to load a second model when the development service reports an active one; it unloads its owned process and does not clean weights or projects. Further qualification needs repeated sampling, independent expert review, realistic held-out reports, adverse inputs, native Windows runtime measurements and a predefined scoring rubric.
