# Preliminary local assistant evaluation

Development observations, **17 October 2026**, source milestone 0.1.9. This is a small engineering smoke test, not a biological benchmark, model ranking or a claim of validated interpretation.

## Current model: Gemma 4 12B (0.1.9)

The selected replacement is official Google Gemma 4 12B Instruct QAT Q4_0. See [the complete Gemma evaluation](GEMMA_EVALUATION.md) for real answers, observed failures, integration corrections and retests. This is an experimental interpreter, not a validated biological agent.

## Liquid comparison

A fresh paired diagnostic run retained Gemma and rejected Liquid as its replacement in this integration. See [the full Liquid/Gemma comparison](LIQUID_COMPARISON.md) for eight cases per model, tool failures, observed timings, exact profiles and remaining scientific errors in both models. Draft-return counts are not accuracy scores.

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
