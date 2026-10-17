# Interpretation, channel identity and display verification — source 0.2.4

This milestone improves the existing analysis workflow. It does not add denoising, deconvolution, autonomous ROI drawing or a replacement model. Private microscopy files, annotations and detailed local reports are excluded from the public update.

## Channel identity and acquisition checks

The authenticated channel-name endpoint requires the current expected image metadata, retains original imported names, preserves native channel order and source bytes, and rejects missing/duplicate/oversized names. Names survive same-series/axis reinspection. Historical reports remain on disk; their prior metadata cannot silently become a new marker assignment. The interface preserves drawn ROIs and clears affected current reports so they can be recalculated with the new labels.

The selected-plane quality endpoint reads all native pixels, rather than a display thumbnail. It records min/max, mean/population SD, zeros and storage-ceiling occupancy. It distinguishes constant/all-zero values from missing calculations. Storage bit depth is not assumed to be the detector's effective bit depth: clipping below the storage maximum can remain undetected. These checks do not measure bleed-through, registration, antibody specificity or biological validity.

Experiment comparison now requires selected channel identities in the completed batch report and rejects names that differ across images at the same selected index. Its algorithm is `experiment-inference-2`. Matching names alone do not validate sample labelling. Historical results remain available; incomplete older batches must be reviewed/recalculated before new comparisons.

## Preview contrast

The main XY and 3D previews default to fixed native storage endpoints, without percentile enhancement. Automatic contrast remains an explicit display option. LUTs, raw measurements and source TIFF bytes remain independent; snapshot details preserve the contrast choice. New volumes default to zero background cutoff; saved cutoff settings remain supported. Volume opacity/integration still affects appearance and must not be confused with calibrated intensity photometry. Original vendor display settings are not reconstructed when unavailable.

The preparation and linked-section displays retain their matched/reference contrast conventions, as documented in the manual. They are not controlled by the main preview selector.

## Independent Fiji comparison

[COLOC2_THRESHOLD_BENCHMARK.json](COLOC2_THRESHOLD_BENCHMARK.json) records 36 deterministic cases from the installed Coloc 2 implementation: unsigned 8/16-bit ranges, independent/positive/negative patterns, full/irregular masks and zero/exact-boundary/above-range thresholds. A deliberately retained positive boundary pixel makes the differing equality predicates observable in twelve cases.

Coloc 2's `Above` mode requires positive opposite-channel intensity and includes equality at its threshold. OrganelleScope uses strict `>`. The benchmark keeps those unaligned differences. Separately, it passes the next representable DoubleType threshold to Coloc 2 to compare identical strict predicates. All 36 aligned cases pass at tolerance 1e-10; the largest absolute difference is 4.440892098500626e-16. This is not automatic Costes threshold-search parity, a Costes randomization test, JaCoP equivalence, or biological validation.

## Assistant interpretation

The existing Gemma weights and local read-only tool boundaries remain. Before generation, the assistant receives a deterministic reading guide with matching segmentation, cuboid, selected-plane quality and experiment reports, plus selected cached STRING/KEGG evidence. Per-image summaries require matching source hash and image metadata; experiment summaries require the selected batch ID. These are supplied application records, not independent remeasurement by the LLM. Detailed reports can be bounded; exports remain authoritative.

Answers expose application-generated interpretation notes separately from generated prose. The guide distinguishes undefined versus unperformed calculations, zero-threshold overlap, threshold-defined objects, edge truncation, occupied-voxel proximity, experimental units and hypotheses. No biological certainty is assigned automatically. Selected evidence is supplied without an implicit online refresh. General questions still work without saving or an image.

Synthetic-only real-model observations and their limitations are preserved in [the initial run](ASSISTANT_INTERPRETATION_BENCHMARK.json) and [the follow-up](ASSISTANT_INTERPRETATION_FOLLOWUP.json). These are one sampled draft per scenario, not an accuracy estimate or an independent biomedical benchmark. Changes to prompt/context/runtime cannot be attributed to model weights. An initial timeout is retained rather than counted as a correct answer. Completion requests now allow up to five minutes per model call, accommodating slow local generation; status checks retain their short timeout. The assistant can still produce fluent errors and requires review.

## Documentation and release boundaries

MANUAL.md now includes 32 numbered references, including thirteen added primary scientific papers, with citations at relevant methods and interpretation points. Citations support the concepts described, not application certification. No separate viewer-inspired roadmap is reintroduced.

Automated source tests, the production UI build, live preview checks and a packaged-backend synthetic smoke test are recorded in SOURCE_VERIFICATION_0.2.4.json. Source execution and packaged execution are separate checks. Native Windows installation, signing/notarization, realistic design-specific statistical coverage and independent biological validation remain open gates. The compact installer does not bundle Gemma's multi-gigabyte weights.
