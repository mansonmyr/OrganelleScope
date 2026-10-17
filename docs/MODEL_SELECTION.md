# OrganelleScope model selection and replacement rationale

Decision record · 17 October 2026 · source 0.2.2. This is a literature and integration assessment, not a new inference benchmark. No candidate weights were downloaded, and the active model was not replaced.

## Decision

Retain **Gemma 4 12B Instruct, official QAT Q4_0**, as the default local text assistant. This is an operational decision based on the working integration and its recorded local evaluations, not a claim of superior biomedical accuracy. Known qualitative errors remain in [Gemma evaluation](GEMMA_EVALUATION.md). The previous [Liquid comparison](LIQUID_COMPARISON.md) and [assistant evaluation history](ASSISTANT_EVALUATION.md) remain part of the accumulated record.

If one model must be shipped, retain Gemma until a challenger passes the same application-specific evaluation. If optional vision becomes a priority, evaluate image support for this same Gemma checkpoint/runtime first, alongside Qwen2-VL-7B. Do not assume a second model is necessary simply because today's integration is text-only.

## Correcting the text-only distinction

Google's current [Gemma 4 12B model card](https://huggingface.co/google/gemma-4-12B-it) describes an encoder-free unified architecture accepting multimodal inputs. **The upstream model is not inherently text-only.** OrganelleScope currently sends metadata, native engine reports and evidence records as text; it does not send microscopy pixels, image patches or a rendered volume to the model. The pinned GGUF/runtime vision path has not been qualified here. Enabling images requires checking conversion contents, runtime support, image preprocessing, prompt formatting and actual local inference. Earlier documentation that says “text-only use” describes the application configuration, not the model family's theoretical capability.

The active file is `gemma-4-12b-it-qat-q4_0.gguf`, 6,975,879,296 bytes (6.98 decimal GB; about 6.50 GiB), SHA-256 `93567e57a8fe10b23569b9d9ec38cd005deedf71e29477c421a4b83f418a538b`. This file size is not peak unified memory. The application caps context at 8,192 tokens and runs a bounded read-only tool loop. See [local assistant configuration](LOCAL_ASSISTANT.md).

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
