# Viewer ideas informed by napari

Assessment · 17 October 2026. **Roadmap only**, except the channel LUT controls implemented in source 0.2.2. No napari dependency, plugin installation, Python console or code transplant is introduced.

## What napari already provides

[napari](https://github.com/napari/napari) is an established multidimensional viewer with Image, Labels, Points, Vectors, Shapes and Surface layers, 2D/3D viewing and extensibility. Its [Image layer guide](https://napari.org/stable/howtos/layers/image.html) documents channel/layer display controls; its [Labels guide](https://napari.org/stable/howtos/layers/labels.html) documents editable label images. These are mature design references. The ideas below do not claim that napari or its plugins cannot implement similar workflows. Any later reuse of upstream code must retain the applicable BSD-3-Clause notices; independently referencing a workflow does not make OrganelleScope a napari-based application.

## Priorities for OrganelleScope

| Priority | Reference idea | Proposed OrganelleScope workflow | Scientific purpose | Acceptance criteria / status |
|---|---|---|---|---|
| Now | Per-channel colour maps | Independent LUT dropdowns in Channels, consistent XY/3D/linked-section/preparation displays and snapshot provenance | Make channels interpretable without changing numerical results | Implemented; native pixels and quantitative reports invariant under LUT changes |
| 1 | Layer list and display controls | A source-aware layer inspector: raw image, processed comparison, reviewed ROIs, cuboid and threshold surfaces identified separately; visibility never silently selects measurement source | Prevent measuring a different representation from the one the user thinks was selected | Proposed; saved visible-state provenance, explicit source badges, no stale result reuse |
| 2 | Linked labels and object properties | Select a segmented object in a section/table, highlight it across views, inspect its bounds, channel intensities, threshold recipe and boundary flag | Audit whether the measured object corresponds to the intended structure | Proposed; stable selection within one result, explicit invalidation on resegmentation, no biological identity assigned by colour |
| 3 | Shape editing | Undoable ROI/mask edit history with before/after measurement deltas and a review queue | Show the effect of subjective boundary changes | Proposed; source-coordinate editing, versioned undo, batch review invalidated on edits, original mask retained |
| 4 | Shared coordinates and slicing | A calibration/provenance inspector linking cursor position, source indices, physical coordinates, registration status and optical-resolution notes | Distinguish known sampling from unmeasured registration/PSF uncertainty | Proposed; unknown uncertainty stays unknown; metadata must not become an invented error bound |
| 5 | Reusable workflows | A processing/threshold sensitivity notebook generated from actual engine runs, with raw/processed metrics and recorded rationale | Expose dependence on analytical choices and discourage selecting only a favourable setting | Proposed; preregisterable setting ranges, complete run history, identical ROI/source, multiplicity explained |
| 6 | Multiscale and lazy images | A tiled preview/cache engine, keeping explicit full-resolution analysis separate | Improve 2048² four-channel stack responsiveness without changing results | Proposed; memory/stress benchmarks, cancellation, bounded cache, exact crop parity and visible preview sampling |

## A distinct direction

OrganelleScope should connect **source → calibration → display → reviewed ROI/object → analysis choice → experiment comparison → evidence → interpretation** in a single inspectable record. A future “Why did this result change?” view could compare two recorded runs, identify changed ROI boundaries, background/threshold choices and excluded objects, then show the actual metric differences. The assistant could explain these recorded differences with citations; it would not regenerate measurements.

This is a product direction, not a claim of algorithmic novelty, better accuracy or exclusive capability. The advantages need user testing and comparison against a specified napari/plugin configuration. Start with the layer/source inspector, then linked object review. Do not implement an unrestricted console or autonomous ROI drawing merely to match a general viewer's feature list.

## Validation before each milestone

Use deterministic synthetic geometry, independent numeric references, saved-project round trips, input-invalidation tests and actual UI interaction. Check scientific interpretation with representative acquisitions/controls when available. Biological validation remains deferred at the user's request; it cannot be replaced by synthetic tests or by borrowing a mature viewer's interface pattern.
