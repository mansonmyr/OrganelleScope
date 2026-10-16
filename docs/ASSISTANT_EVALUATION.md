# Preliminary local assistant evaluation

Development observations, **17 October 2026**, source milestone 0.1.7. This is a small engineering smoke test, not a biological benchmark, model ranking or a claim of validated interpretation.

## Configuration

Apple M3 / 24 GB unified memory; Qwen3.5-4B community Q4_K_M (exact size/hash/revision in LOCAL_ASSISTANT.md); official llama.cpp b11669, Metal, four CPU threads, one slot, 8,192-token context, thinking disabled, temperature 0.2. No vision projector or raw microscopy image was passed to the model. The assistant used saved source metadata and deterministic reports from the existing synthetic validation stack (64×64, eight Z planes, two channels; XY spacing 0.1 µm, Z spacing 0.4 µm).

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
