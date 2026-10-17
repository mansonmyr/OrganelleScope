# Capability comparison and release-readiness criteria

Reviewed 16 October 2026. OrganelleScope column refers to source milestone 0.1.9 (OrganelleScope status updated 17 October 2026), not an installed release. Other applications are described using primary documentation; they were not all installed or benchmarked for this review. This document separates feature presence from scientific validation, workflow completeness and production readiness.

## How to interpret the comparison

- **Built-in:** implemented in the component being compared. A plugin is not automatically part of every host installation.
- **Host/plugin dependent:** possible through the named ecosystem; identify the exact version, module and parameters before evaluating a workflow.
- **Planned:** not implemented in OrganelleScope. A UI placeholder, source plan or numerical unit test does not establish a functioning validated feature.
- **Not assessed:** no sufficiently specific evidence was reviewed; it must not be read as a definitive absence.

No overall quality score is assigned. Scientific accuracy, speed, large-data stability and ease of use need controlled, reproducible experiments. A feature checklist cannot establish those outcomes or publication suitability.

## Dedicated colocalization workflows

| Criterion | OrganelleScope | Fiji/ImageJ + JaCoP family | Fiji/ImageJ + Coloc 2 | CellProfiler |
| --- | --- | --- | --- | --- |
| Quantitative approach | Explicit intensity metrics in XY ROIs and 3D cuboids | Multiple correlation/overlap methods and object-based options | Pixel-intensity correlation/overlap, thresholding and significance | Image- and object-level colocalization module |
| Pearson / Manders | Implemented with documented denominators and unavailable cases | Documented tools | Documented tools | Dedicated module; verify selected metric options |
| Alternative correlation methods | Spearman implemented; Li/Van Steensel not implemented | Li/Van Steensel tools documented | Li and other pixel-intensity methods documented | Module-specific; match settings before comparison |
| Thresholding | Manual/zero; Costes-style automatic on raw integer images only | Costes tools; behavior depends on variant/settings | Automatic thresholding supported | Configurable module settings; inspect exact implementation |
| Spatial chance assessment | One explicitly conditional whole-plane toroidal-shift test | Costes randomization tools documented | Statistical significance testing documented | Not assessed here; a correlation measurement alone is not a spatial significance test |
| Object-based colocalization | Planned; a cuboid is not object segmentation | Object-based options, variant dependent | Explicitly outside Coloc 2's scope | Can measure within identified objects; do not equate this with every object-distance method |
| 3D | Full-resolution cuboid measurements, linked slices and preview | Stack behavior must be checked for the chosen variant | Z stacks documented | MeasureColocalization documents 3D support |
| Numerical equivalence to others | Not established; independent comparisons pending | Must match masks, threshold rules and version | OrganelleScope does not claim to replicate its algorithms | Must match masks, intensity scaling and module settings |

Sources: [ImageJ colocalization overview / JaCoP](https://imagej.net/imaging/colocalization-analysis), [JaCoP project entry](https://imagej.net/ij/plugins/track/jacop.html), [Coloc 2 documentation](https://imagej.net/plugins/coloc-2), [CellProfiler 4.2.8 measurement documentation](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.2.8/modules/measurement.html#measurecolocalization). JaCoP classic and BIOP variants are distinct benchmark configurations. The CellProfiler document version is a reviewed reference, not a claim about the newest release.

## Broader image-analysis applications

| Application | Documented strength | Integration / extensibility | Appropriate comparison task |
| --- | --- | --- | --- |
| napari | Multidimensional layers, 3D visualization and interactive annotations | Python and domain plugins | Calibrated stack display, annotation and performance using specified plugins; no assertion that the base viewer bundles a dedicated colocalization suite |
| QuPath | Large-image/tissue workflows, fluorescence/multiplex analysis, objects and classification | Projects, scripts and extensions | Tissue/cell quantification and reproducible project/batch workflows; its principal use case differs from confocal organelle volume rendering |
| Icy + ColocalizationStudio workflow | Documented detection and object-colocalization protocol | Protocols, scripts and plugins | Spot-detection/object-colocalization with the same detections and distance criteria |
| Imaris Essentials / Coloc | Commercial interactive volume/surface visualization, colocalization and object-distance/overlap workflows | Product/package-specific tools | 3D region/surface analysis and usability on matched datasets; package entitlement must be stated |

Sources: [napari quickstart](https://napari.org/stable/getting_started/quick_start.html), [QuPath project](https://github.com/qupath/qupath/blob/main/README.md), [QuPath multiplex tutorial](https://qupath.readthedocs.io/en/latest/docs/tutorials/multiplex_analysis.html), [Icy object-colocalization protocol](https://icy.bioimageanalysis.org/protocol/spot-detection-and-colocalization-object-analysis/), [Imaris Essentials](https://imaris.oxinst.com/products/imaris-essentials).

## Biological evidence integration

OrganelleScope currently provides human STRING identifier mapping and association-network tables, academic KEGG membership lookup and on-demand official pathway diagrams. It records identifiers, source versions/timestamps and response hashes, and keeps image measurements local. The experimental local assistant can inspect saved measurements/evidence and repeat a bounded saved query, with visible tool records. It is not validated biological interpretation, enrichment analysis, pathway activation measurement or a causal perturbation model.

Equivalent end-to-end STRING/KEGG integrations were not systematically surveyed across every plugin and extension of the other applications. Accordingly, neither the README nor this document claims that they cannot provide them. The intended distinction is a guided, traceable combined workflow, not invention of correlation metrics or a proven exclusive capability.

## What a mature OrganelleScope release must demonstrate

| Area | Current evidence | Required release gate |
| --- | --- | --- |
| Import fidelity | Supported TIFF axes/scale fixtures and source fingerprints | Representative acquisition formats, malformed files, large stacks and independently verified metadata |
| Quantitative correctness | Analytic/SciPy checks and explicit conventions | Matched independent JaCoP/Coloc 2/CellProfiler results; documented expected differences |
| Spatial inference | One seeded translation model with applicability warnings | False-positive calibration, compartment-aware alternatives, sensitivity and multiplicity control |
| Biological experiments | Descriptive image/ROI results | Independent experiment/cell identifiers, effect sizes and uncertainty without pseudoreplication |
| 3D quantification | Source cuboids and linked sections | Inspectable organelle masks, surfaces and distances; registration/resolution uncertainty |
| Preprocessing/restoration | Deterministic background subtraction and smoothing | Noise2Void/model validation, residuals, held-out acquisitions and downstream measurement bias |
| Projects / automation | Manual versioned local projects retain source associations, settings and workspace reports; round-trip tests | Portable archives, multi-image experiments, batch runs, cancellation, autosave and recovery |
| Evidence reliability | Explicit mapping, live checks, caching, diagrams and provenance | Provider failure/changed-schema handling, rights review, stable exports and evidence review |
| Local agent | Experimental pinned Gemma 4 12B Instruct QAT Q4_0 / llama.cpp; local tool loop, response checks, recorded quantities, visible audit; M3 smoke tests | Curated biological/citation-entailment and adversarial evaluation; native Windows qualification; offline installer and dependency review |
| Distribution | Development packaging and Mac signing fixes | Native platform installations, memory/performance budgets, production signing and release procedures |

## Independent benchmark protocol to implement next

Use versioned synthetic fixtures and representative research images with identical channel pairs, ROI masks, source intensities, calibration and thresholds. Compare Pearson, Spearman where available, Manders numerators/denominators, threshold edge cases, undefined values and 3D voxel inclusion separately. Record exact tool/plugin versions and expected algorithm differences. Compare spatial tests only when the null models and sampling rules match; do not rank incompatible p-values. Add blinded controls and independent-experiment replication before drawing biological conclusions. No benchmark result is claimed in this document.
