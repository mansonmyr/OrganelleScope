# OrganelleScope Manual

## A practical guide to calibrated microscopy, measurements and interpretation

**Edition 1.0.2 · 18 October 2026 · local research workbench**

This manual documents version 1.0, including channel identities, signal checks, native-range previews, recorded measurements and evidence-assisted interpretation. Use the matching release notes and platform verification assets for the installed version. See the [verification record](docs/VALIDATION.md) for the scope of numerical and native installation checks.

OrganelleScope combines workflows from the Probabilistic Colocalization Estimator and Quick IF Line Profiler. It keeps microscopy images local, connects explicit measurement choices to saved results, and offers optional database context and a supervised local assistant. It does not convert conventional fluorescence images into validated super-resolution acquisitions, identify molecular binding from overlap, or certify publication readiness. The supplied owner-reviewed microscopy regions support scoped workflow checks. Independent population-level biological accuracy and general assistant accuracy are outside the established evidence. Numerical verification and biological validation answer different questions.

### First installation and retained data

A first installation in a new operating-system account starts with an empty image list and no saved projects. Research images, projects, recovery records and conversations are stored separately in that account’s local application data, never seeded from the developer’s workspace. Installing an upgrade or reinstalling in the same account preserves that account’s existing work; the recent-import list can therefore remain populated. Automatic Gemma setup downloads model weights only, not microscopy images. Source-development sessions may have their own retained local data.

### Contents

- [Part I — Getting started](#part-i--getting-started)
- [Part II — Images and physical calibration](#part-ii--images-and-physical-calibration)
- [Part III — Viewing, channels and snapshots](#part-iii--viewing-channels-and-snapshots)
- [Part IV — Background correction and smoothing](#part-iv--background-correction-and-smoothing)
- [Part V — Drawing and line profiles](#part-v--drawing-and-line-profiles)
- [Part VI — ROI measurements and channel associations](#part-vi--roi-measurements-and-channel-associations)
- [Part VII — 3D cuboids, masks and spatial measurements](#part-vii--3d-cuboids-masks-and-spatial-measurements)
- [Part VIII — Validation and experimental comparisons](#part-viii--validation-and-experimental-comparisons)
- [Part IX — Batch analysis and Excel](#part-ix--batch-analysis-and-excel)
- [Part X — STRING, KEGG and pathway diagrams](#part-x--string-kegg-and-pathway-diagrams)
- [Part XI — Local assistant and model decisions](#part-xi--local-assistant-and-model-decisions)
- [Part XII — Projects, exports and reproducibility](#part-xii--projects-exports-and-reproducibility)
- [Part XIII — Troubleshooting and responsible interpretation](#part-xiii--troubleshooting-and-responsible-interpretation)
- [Part XIV — Development, distribution and comparisons](#part-xiv--development-distribution-and-comparisons)
- [Part XV — Glossary](#part-xv--glossary)
- [References and further reading](#references-and-further-reading)

---

## Part I — Getting started

### 1. Intended questions

Appropriate starting questions include: Is protein X enriched in a marker-defined region? Do two channels vary together within a specified ROI? Does a measured association change between conditions across independent experiments? How sensitive is a result to background correction, threshold or region boundaries? Which reference pathways contain a selected human protein?

Confirm biological identities against the acquisition record or owner annotation for each stored channel. Review proposed candidate ROIs individually: acceptance supports use as selected regions, not verified independent cells. Rejected regions remain in technical reports with their status; an intended negative-control label does not make unsuitable regions valid. If no negative-control regions are accepted, the supplied set cannot establish negative-control discrimination. A filename or dye name is not sufficient: a corrected marker label invalidates earlier marker-specific interpretations, and changing the reference channel requires rerunning candidate ROI selection and measurements. Preserve the superseded report as a labelled provenance record.

A centrosomal marker such as pericentrin or gamma-tubulin can help define a region for a localization experiment; MitoTracker can provide mitochondrial context. The expected relationship is experimental context, not a software ground-truth label. Stain specificity, registration, signal contamination and the exact cellular condition still need consideration. Naming a mask “centrosome” does not verify its identity. The same manual workflows can be applied to nuclear, mitochondrial, Golgi or microtubule marker images, but no specialized organelle classifier is included.

### 2. Platform and installation

The deployment targets are Apple Silicon macOS and Windows 11 x64. The development host is an M3 Mac with 24 GB unified memory. Release candidates include automated native Windows x64/macOS ARM64 installation/startup checks and synthetic frozen-service workload reports. These do not replace human interaction and representative acquisition testing. A Windows ARM virtual machine is not a substitute for native x64 hardware validation.

A packaged installation contains an Electron interface and a local Python analysis executable; the user does not need to install Python for the packaged analysis service. The installer includes the llama.cpp runtime. On first launch, it automatically downloads the pinned approximately 6.98 GB Gemma weights into application-managed storage, checks the full SHA-256 digest, then installs them atomically. A progress banner offers pause/resume; interrupted downloads resume when supported by the provider, otherwise restart safely. Paused/error setup does not silently restart on every launch. Image analysis remains available during setup. No image or conversation is sent with the weight request. Internet is required once for setup; subsequent local inference works offline. See [assistant operation](#47-what-the-assistant-can-do).

On macOS, open the DMG, copy the application into Applications and open it. Current development packaging verifies an ad-hoc signature. It is not Apple Developer ID signing or notarization. For an unidentified-developer message, use Apple's app-specific guidance only after checking that the download is the intended build. A damaged-app message can also reflect corruption or invalid signing; do not assume every such warning is harmless and do not disable Gatekeeper globally. Record the filename, version and checksum when reporting installation trouble. [Apple guidance](https://support.apple.com/en-us/102445); [packaging history](MANUAL.md#2-platform-and-installation).

### 3. First complete workflow

1. Open **TIFF / OME-TIFF**, select the correct series and inspect import notes.
2. Confirm axes, channel identities and physical spacing. Resolve ambiguous or conflicting metadata before physical interpretation.
3. Inspect several Z planes in the persistent preview. Choose LUTs for clarity, not to increase apparent overlap.
4. In **Background correction**, compare a justified recipe with the raw image. Applying a recipe makes it available; it does not automatically make every measurement processed.
5. Draw a line, circle or polygon. In **ROI measurements**, select raw or processed intensities, threshold mode and regression target, then calculate.
6. Read channel summaries and **Channel associations**, including undefined-value explanations. Use **3D workspace** for linked sections, a full-resolution cuboid and optional threshold-defined objects.
7. Use **Validation** to examine numerical references, preparation sensitivity and an appropriate conditional spatial control.
8. Use **Batch analysis** for independently reviewed images and **experiment comparison** for correctly labelled biological units.
9. Optionally retrieve STRING/KEGG evidence or ask the local assistant. Keep observed data, database context and hypotheses separate.
10. Save a project or batch, export full JSON and retain original acquisition files. A snapshot is a presentation artifact, not a quantitative source image.

### 4. Interface map

The **Workspace** sidebar contains image import, recent imports, collapsible **Projects & recovery** (save/open, portable archives and recovery), source information, calibration and **Channels**. Project controls no longer occupy horizontal bars above the preview. The shared top preview has independent **XY slice / 3D preview** modes and capture controls. The drawing dock is below the XY image. Workspace tabs below the preview open Image & ROI, Background correction, ROI measurements, Channel associations, 3D workspace, Validation, Molecular evidence, Batch analysis and Local assistant. Smaller windows use a **Workspace** dropdown for the same destinations. Switching workspaces does not replace the shared preview. Preview mode is a separate choice.

---

## Part II — Images and physical calibration

### 5. Supported data and axes

The importer reads TIFF, OME-TIFF and supported ImageJ TIFF metadata with native unsigned 8- or 16-bit pixels, one to four channels and static XY images or Z stacks. Pairwise colocalization requires at least two usable channels. An 8-bit channel has a storage range of 0–255; a 16-bit channel has 0–65,535. A 12-bit detector stored in a 16-bit TIFF need not use the full 16-bit range. Storage bit depth does not establish detector linearity or photon counts.

Axes mean **X** horizontal pixels, **Y** vertical pixels, **Z** depth planes, **C** channels and **T** time. `CZYX` and `ZYXC` are different layouts. The file's source axis letters can include samples (`S`) for RGB components. Review the confirmed axis mapping rather than inferring channel count solely from the number of TIFF pages. A series is one image dataset inside a multi-series TIFF, not necessarily one channel. Time-lapse analysis is excluded: an interpreted time dimension greater than one must not be treated silently as a static Z stack.

Rendered RGB exports can contain colour components rather than separate quantitative acquisition channels. The importer reports this possibility. Recolouring RGB components cannot restore the original acquisition signals. Prefer unmerged source channels when quantifying biological relationships. Super-resolution image rasters can be inspected when they meet supported TIFF requirements, but the current app has no STORM/PALM localization-table pipeline, localization-precision model or raw-movie reconstruction.

### 6. What metadata is extracted

The sidebar shows file identity, storage dtype, dimensions, source/confirmed axes, series, decoded-size estimate, channel labels, calibration candidates and acquisition information when present. Metadata availability depends on the writer. OME physical sizes and available plane information, ImageJ units/spacing and TIFF resolution tags are inspected. Missing values remain missing. Inherited ImageJ Info dimensions that disagree with the actual stored TIFF now produce an explicit warning; an original acquisition saying three channels does not recreate channels omitted during export. A microscope's generic specification cannot substitute for the actual objective, zoom, binning and acquisition settings of an image.

OME pixel size is not the same as print DPI. Generic TIFF resolution tags can describe page printing rather than specimen scale. Conflicting sources are surfaced for review; an explicit user override is recorded. **Apply import settings** reinspects the association and invalidates affected analyses. Retain the reason for an override in your laboratory records. [OME data model](https://docs.openmicroscopy.org/ome-model/6.2.3/ome-tiff/); [import implementation](backend/organelle_scope/image_io.py).

### 7. Physical calibration, sampling and resolution

X/Y spacing are specimen distances per pixel; Z spacing is the step between successive planes. With spacing `sx`, an X index difference of `dx` corresponds to `dx × sx`. For an XY mask containing `N` selected pixel centers, area is `N × sx × sy`. For a cuboid with `N` selected voxels, region volume is `N × sx × sy × sz`. Unknown spacing makes the associated physical quantity unavailable; it does not turn it into zero.

A pixel is a sample, not a molecule. Optical resolution concerns the ability to distinguish nearby structures and depends on the acquisition, PSF and analysis. Finer displayed pixels or interpolation do not create additional resolved information. Channel registration error, axial uncertainty, PSF width, antibody/linker offsets and localization error are not inferred from metadata or user-entered spacing. The physical-calibration information pop-up explains these distinctions in the app.

For 15 planes with 0.315 µm Z spacing, the first-to-last plane-center span is `(15 − 1) × 0.315 = 4.410 µm`; the corresponding 15-voxel coverage convention is `15 × 0.315 = 4.725 µm`. Both can appear in software descriptions. Report which convention is used. OrganelleScope's cuboid volume and displayed voxel extents use voxel counts times spacing; coordinates and crosshair offsets refer to plane/pixel centers. The first plane is index zero in JSON and plane one in the interface.

### 8. Size and performance boundaries

The import upload cap is 8 GiB per TIFF. Decoded size is an estimate of array storage, not peak memory; decompression, float processing, rendering and model inference add allocations. Supporting uint16 2048 × 2048 data does not establish responsiveness for every four-channel stack depth. Large real-stack stress qualification remains incomplete. A small failed or rejected request should produce an actionable error rather than silent downsampling of quantitative measurements. Save work before unusually large operations.

---

## Part III — Viewing, channels and snapshots

### 9. Channel identities and LUT controls

In the Workspace sidebar, enter a name for each stored channel under **Channels**, then choose **Apply channel names**. Assign names from acquisition records or your experimental labelling scheme; do not infer a protein from its dye, LUT colour or filename. Names must be distinct and are kept in native channel order. The app preserves the original imported names and records the assignment as user supplied. The TIFF bytes, source hash and quantitative intensities are unchanged. Reinspection retains names when the series, axes and channel count are unchanged; a changed axis interpretation or series requires reviewing identities again.

Applying names keeps drawn ROIs and display settings, but invalidates existing current-image reports so old marker identities cannot be silently presented as new results. Recalculate and save a new project revision. Earlier saved projects retain their earlier image metadata; opening one may create an isolated image association to preserve that revision. New reports, snapshots, batch exports and assistant context use the applied names.

Choose **Check selected-plane signal** to read every raw pixel of the current XY plane. The report records channel minimum, maximum, mean, population SD, zero count and pixels at the storage ceiling. For unsigned 16-bit storage that ceiling is 65,535, even if the detector originally used fewer effective bits. The check therefore labels detector saturation as **not determined**. A channel can clip at a lower acquisition ceiling; absence of storage-ceiling pixels does not prove there was no clipping. All-zero or constant channels make correlation undefined, rather than proving biological absence. The check concerns this plane only, not every Z plane, ROI or cell. Bleed-through, misregistration, antibody specificity and independent replication require additional evidence. See [Waters 2009](#ref-waters2009), [Jost & Waters 2019](#ref-jost2019) and [Montero Llopis et al. 2021](#ref-montero2021).

#### Display LUT controls

A **lookup table (LUT)** maps normalized display intensity to colour. In **Channels**, each acquisition channel has its own dropdown: Rose, Mint, Ocean, Silver, Red, Green, Blue, Cyan, Magenta, Yellow, Grayscale or Orange. These are linear black-to-colour maps. They are false-colour display choices, not changes to fluorophore identity. Choosing cyan for one marker and magenta for another can make their contributions easier to distinguish; colour choice alone is not an analysis method.

Selections apply to the selected single-image workspace's XY preview, VTK volume, linked sections, preparation/background previews and line-chart colours. Captures inherit their displayed colours. The segmentation label/mask surface uses an annotation colour to distinguish geometry; it is not another acquisition-channel LUT. Batch queue images retain their separate viewing context and default colours; the single-image sidebar does not recolour unrelated queued images. The batch workflow does not yet expose per-item LUT editing.

LUT selections are saved with the project and recovery workspace and recorded in inspection/snapshot details. **Reset channel LUTs** restores the standard per-channel palette. Changing a LUT does not change source TIFF pixels, masks, ROI geometry, background recipes, thresholds, channel order, regression target or statistical results. It does not clear a valid measurement. Existing projects without LUT settings use defaults. This follows the distinction between display colour and measurement emphasized in [ImageJ's colocalization guide](https://imagej.net/imaging/colocalization-analysis).

### 10. Display contrast and composites

The main **Preview contrast** control defaults to **Native range · no automatic enhancement**. Each channel maps zero to black and the unsigned storage maximum to full LUT colour: 0–255 for 8-bit data or 0–65,535 for 16-bit data. There is no per-image percentile stretch, gamma adjustment or offset in this mode. Low-valued data stored in 16-bit TIFFs can appear very dim. This is expected and does not mean measurements lost signal. The app cannot promise the microscope vendor's original appearance when acquisition display settings are absent or unsupported.

**Automatic contrast · display only** is optional. In XY it estimates each channel's upper ceiling from a sampled 99.5th percentile, falling back to the maximum or one for degenerate images. Switching contrast never changes measurements, thresholds or source bytes. Channels are coloured and added, with the composite clipped to the display range. Display saturation in a merged PNG is different from raw detector clipping. XY previews remain thumbnails bounded to 1024 × 1024. [Waters 2009](#ref-waters2009) explains why acquisition and display must be distinguished.

The main 3D preview uses the same contrast choice: native storage endpoints by default, or a sampled nonzero-voxel percentile in automatic mode. Ray integration, opacity, background cutoff, lighting and downsampling still affect its appearance: a volume is not an unmodified intensity photograph. New workspaces default to no background cutoff; saved workspaces retain their recorded cutoff. Changing contrast rebuilds the volume and can reset its camera. Snapshots record contrast mode, LUTs and the relevant display settings. Save/export snapshot details for reproducibility.

The preparation comparison and linked sections retain their separate matched/reference contrast conventions; the main preview selector does not change these analytical comparison displays. Preparation uses the same raw-derived ceiling for raw and processed panels so subtraction is not hidden by independent enhancement. Across conditions, compare recorded intensities under matched acquisitions and recipes; an automatically brightened screenshot is not a calibrated intensity comparison.

### 11. XY navigation

Pinch the trackpad or scroll over the XY image to zoom about the pointer. Zoom is 25–800% of the fitted view, not a calibrated magnification or source-resolution measure. Toolbar buttons and a slider offer alternatives. **Pan image** enables dragging; turn it off to draw ordinary ROIs. Space-drag or middle-button drag temporarily pans. Panning moves the viewport, not the ROI. **Fit image** resets display zoom and scroll position.

The SVG drawing layer keeps the native source-coordinate view box as the image enlarges. Inspect a known object after a zoom change if you are uncertain whether a gesture drew or panned. A Z-plane change selects a different native plane; existing area ROIs remain attached to their recorded plane. A temporary line is cleared when changing plane.

### 12. 3D preview

Choose **3D preview**, then all channels or an individual channel. Drag rotates; scrolling and explicit zoom buttons change the camera. Reset view reframes the volume. The renderer uses bounded downsampled data; it is independent of full-resolution cuboid/mask calculations. Physical proportions require known XYZ spacing. Otherwise the view is explicitly voxel-space, with no inferred physical depth.

Cutoff and opacity alter visibility, not the voxel measurements. Display Z stretch exaggerates depth for inspection; it is not new Z calibration. LUT changes update colour transfer functions without intentionally resetting the active camera. Rendering transparent/low-intensity material can make a volume appear thin; inspect XY/XZ/YZ source sections before concluding that Z information is absent. No 10 nm or super-resolution claim follows from rendering a small-looking structure.

### 13. Capturing a preview

**Capture PNG** exports the current XY plane or rendered 3D camera view. XY optionally includes visible ROIs and the line. XY inspection zoom does not crop the export: it captures the whole displayed plane, at the preview image's natural dimensions. The 3D capture includes a currently displayed threshold surface and camera/view settings. These behaviours differ deliberately: a volume snapshot captures its camera, whereas an XY snapshot preserves the entire plane.

**Export snapshot details** supplies JSON with source identity/hash, timestamp, calibration, view type, Z/channel selection, LUTs and relevant overlays/settings. Keep it beside the PNG. A PNG is an 8-bit presentation composite; it does not preserve native unsigned/float channel intensities or replace the TIFF, mask labels or engine report. Changing a LUT after a capture does not retroactively change an already exported image. Chart export buttons provide presentation outputs supported by that chart; full measurement records should be exported separately.

---

## Part IV — Background correction and smoothing

### 14. Choosing a measurement source

The main explorer/volume show raw acquisition intensities with display scaling. **Background correction** offers a raw/processed comparison, estimated background and absolute residual views. Apply a recipe, then explicitly select processed data in the relevant ROI/profile/cuboid/mask workflow. A recipe existing in the workspace does not establish that a result used it. The request and recipe hash in the report are authoritative.

Processing is performed per channel, per full XY plane; it does not mix channels or smooth along Z. Full-plane processing precedes ROI/cuboid cropping. Only selected source pixels/voxels enter the regional summary, but their background estimate can depend on neighbouring XY pixels outside the region. Raw TIFF bytes remain unchanged. Processed values use float32; subtraction clips negatives to zero before optional smoothing. Recipe provenance identifies the operation order, boundary handling, settings, software versions and hash.

### 15. Available methods and parameters

| Method/parameter | Meaning | Practical interpretation |
|---|---|---|
| No subtraction | Retain recorded signal | Default baseline; does not prove negligible background |
| Constant offset | Subtract one supplied value per channel | Appropriate only when a spatially uniform background estimate is justified; zero is not an estimated background |
| Square opening | Subtract grayscale morphological opening using a `(2r + 1) × (2r + 1)` square | Models a slowly varying background with a flat spatial footprint; differs from a curved rolling ball |
| Rolling-ball background | Curved lower-envelope estimate with disk support | Assumes bright structures on darker background; large structures can be interpreted as background |
| Radius, XY pixels | Spatial footprint size | Opening: 1–512; rolling ball: 1–100. These are operational bounds, not biological recommendations |
| Ball height | Curvature scale in native intensity units | Positive, up to 65,535; if absent it follows radius numerically, without equating intensity units to physical distance |
| Gaussian sigma | Standard deviation in XY pixels | 0 disables; supported range 0–5. A larger sigma smooths more strongly and can alter correlations and widths |

Rolling ball is implemented as a nonflat SciPy grayscale erosion: for a disk-supported curved kernel `K(q) = h sqrt(1 − ||q||²/r²)`, the background at `p` is `min_q[I(p+q) + h − K(q)]`. Outside-image samples are excluded. This is the implemented convention; byte-for-byte ImageJ rolling-ball equivalence is not claimed. Square opening and Gaussian filtering use reflected boundaries; Gaussian truncation is four standard deviations. See [current implementation](backend/organelle_scope/processing.py), [SciPy grayscale erosion](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.grey_erosion.html) and [Gaussian filter](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html).

No universal background radius or height is inferred reliably from microscope metadata. A default inactive radius of 20 pixels is an editable starting entry, not a validated value. Choose settings against expected structure sizes, independent background regions and controls. Empty numeric preparation fields remain empty while editing and block Apply when required; deleting a value must not silently assert zero.

### 16. Why processing can appear unchanged

A method must be selected and **Apply recipe** pressed. Constant offset zero and Gaussian sigma zero make no change. A sparse image whose background is already near zero may show little subtraction, particularly under its display scaling. A large native dynamic range can hide small changes visually. Do not infer failure or success from appearance alone: inspect estimated background, residual and numeric diagnostics. Increasing subtraction until an image looks clean can erase genuine diffuse signal.

Scientific context: background estimates, bleed-through and intensity thresholds affect the biological meaning of overlap; there is no universally validated background radius for all structures. [Dunn et al. 2011](#ref-dunn2011) and [Bolte & Cordelières 2006](#ref-bolte2006) discuss these dependencies. Removing background is not a substitute for appropriate acquisition controls.

### 17. Diagnostic values

| Output | Definition / interpretation |
|---|---|
| Raw/processed mean | Mean of the full selected XY plane in native intensity units |
| Raw/processed sum | Sum of the same plane's values; affected by plane size and preparation |
| Estimated background mean | Mean background estimate before subtraction/clipping/smoothing |
| Residual mean | Mean of raw minus processed; sign describes net intensity shift |
| Residual RMSE | `sqrt(mean((raw − processed)^2))`; change magnitude, not error against truth |
| Changed pixels | Count with nonzero raw-minus-processed difference |
| Net removed percent | `100 × sum(raw − processed) / sum(raw)`; unavailable for zero raw sum; negative means a net increase |
| Residual neighbour correlation X/Y | Correlation of adjacent residual samples along each axis; undefined if variation is absent |

A structured residual may indicate removed signal; correlated acquisition noise can also be structured. Small RMSE is not evidence of biological correctness. The absolute residual preview is grayscale and combines normalized channel differences; it is a display diagnostic, not a calibrated noise map. Gaussian smoothing remains available, but **Noise2Void and Richardson–Lucy deconvolution were removed at the user's request**. Historical files are preserved; no current training or restoration tool is provided.

---

## Part V — Drawing and line profiles

### 18. Lines, circles and polygons

Use **Line profiler** to drag a start/end line on the selected plane. Use **Circular ROI** to drag from center to edge. Use **Polygonal ROI** to click vertices, then explicitly finish the polygon. Cancel discards an unfinished polygon. Area regions and line profiles are different tools; a line is not a narrow area ROI and a circle's boundary is not a line profile.

Area masks select source pixel centers. Simple polygon boundaries are included; self-intersections/repeated invalid geometry are rejected. A dragged circle is defined in XY pixel coordinates, so unequal X/Y spacing can make its physical shape noncircular. **Apply diameter** sets a physical circle in micrometers and accounts for anisotropic sampling; it can look elliptical in pixel coordinates. A specified 2 µm diameter means a 1 µm radius. The center remains fixed. Regions extending outside the field are clipped with a warning; fewer than three selected pixel centers are insufficient for current ROI statistics.

ROIs belong to their recorded Z plane. Drawing on one slice does not propagate a volume through the stack. Overlapping ROIs can reuse pixels; they do not become independent observations. Redraw to change a boundary/position when the current tool has no direct vertex editing. Deleting/adding/changing a measurement ROI invalidates its displayed analysis until recalculation; mere LUT/zoom changes do not.

### 19. Line sampling and distance

The profile samples native or explicitly processed per-channel planes along the chosen line, using the profile sampler rather than screenshot RGB values. Physical distance along the line uses both X and Y spacing; without complete XY spacing, use pixels. Approximate line-sample interpolation can produce values between source samples. A displayed endpoint difference is not automatically a molecular distance: PSF, registration, marker geometry and labeling offsets remain relevant.

The plotted traces retain sampled intensities. The width estimator uses an approximately three-pixel smoothing operation for peak finding; this is separate from optional image-wide Gaussian preparation. The interface exposes a single-peak FWHM only when a suitable single peak and two half-height crossings are identified. Multiple peaks, missing crossings or insufficient contrast can make width unavailable. The baseline uses a low percentile of the smoothed trace, and crossing positions are interpolated. Algorithm details remain in [profile implementation](frontend/src/workers/analysisCore.ts).

### 20. FWHM interpretation

**Full width at half maximum** is the distance between the left/right crossings at half the peak height above its estimated baseline. It is an apparent signal-profile width. It is not automatically a fluorophore size, organelle diameter, PSF measurement or two-protein separation. The line's orientation, background, smoothing, finite sampling and unresolved adjacent structures can all affect it. An unavailable FWHM is preferable to inventing a width for a truncated or multiplet peak. The UI does not expose every legacy metric helper retained in the source; only visible tools/results are current user features.

---

## Part VI — ROI measurements and channel associations

### 21. Calculation workflow and thresholds

In **ROI measurements**, review the regions, choose intensity source and threshold mode, select the regression target and calculate. **Channel associations** presents pairwise metrics for each ROI. Four channels produce six unordered pairs, with A/B direction preserved for Manders fractions. No pixels from different ROIs or Z planes are pooled into one biological sample automatically.

Thresholds are native intensities, not display brightness, LUT positions or probabilities. Options are zero, manual per channel, or an automatic Costes-style search. Comparisons use strict `>`: a value equal to the threshold is excluded from the other channel's above-threshold condition. Zero threshold includes every positive value, including positive background. Background preparation and thresholds therefore matter greatly for overlap fractions.

The automatic method uses positive total-least-squares regression and searches downward for a valid below-threshold nonpositive correlation. It can be unavailable for nonpositive covariance, constant channels or an unsuccessful search. The secondary threshold is continuous; there is no fallback to the mean. It is **Costes-style**, not a claim of exact Fiji integer-threshold parity. It is currently restricted to raw intensities; processed floating data require zero/manual thresholds. [Exact conventions](MANUAL.md#part-vi--roi-measurements-and-channel-associations).

### 22. Per-channel quantities

| Quantity | Meaning | Interpretation boundary |
|---|---|---|
| Pixel count | Number of centers inside the mask after clipping | Geometric sample count, not independent biological n |
| Area, µm² | Pixel count × X spacing × Y spacing | Discretized selected region, not automatically an organelle area |
| Mean | Sum divided by selected count | Depends on region definition, detector settings and background |
| Sum / integrated intensity | Sum of selected values | Larger regions can have greater sums without greater concentration |
| SD | Population standard deviation of selected intensities | Descriptive heterogeneity, not an uncertainty interval for a biological mean |
| Above-threshold count/fraction | Selected samples meeting the recorded threshold convention | Depends on threshold and recipe; does not identify positive cells automatically |

### 23. Pairwise metric definitions

Let `A_i` and `B_i` be paired channel intensities at the same selected source pixels; `N` is their count. Bars denote ROI means.

| Metric | Formula / definition | What a value means |
|---|---|---|
| Pearson r | `sum((A−mean A)(B−mean B)) / sqrt(sum((A−mean A)^2) sum((B−mean B)^2))` | −1 to +1 linear covariation; zero does not exclude nonlinear association |
| Spearman rho | Pearson correlation of average ranks, including tied values | −1 to +1 monotonic rank association; not spatial distance |
| Manders overlap coefficient, MOC | `sum(A B) / sqrt(sum(A²) sum(B²))` | Uncentered normalized intensity overlap; positive background can inflate it |
| M1 (>0) | `sum(A where B>0) / sum(A)` | Fraction of A intensity at pixels where B is positive |
| M2 (>0) | `sum(B where A>0) / sum(B)` | Reverse direction; different abundance/distribution can give a different value |
| Thresholded M1 | `sum(A where B>tB) / sum(A)` | Fraction of all A intensity at pixels satisfying B's threshold |
| Thresholded M2 | `sum(B where A>tA) / sum(B)` | Reverse direction under A's threshold |

The thresholded denominator in this implementation includes **all** ROI intensity, not only the above-threshold intensity of the numerator channel. Match this convention when comparing another application. Under the app's nonnegative intensities, defined Manders fractions/MOC fall in [0,1]. A value of 0.8 is a fraction under the stated mask/threshold, not an 80% probability of molecular interaction.

Pearson is unchanged by a positive affine rescaling of each channel when nothing else changes. Real background correction with clipping and spatially varying estimates is not simply an affine rescaling. Spearman tolerates monotonic intensity transforms but is affected by ties and changing pixel sets. High M1/M2 with low Pearson can be entirely consistent: signals share positive pixels without proportional intensity variation. Interpreting merged colours alone cannot distinguish these situations. [ImageJ guidance](https://imagej.net/imaging/colocalization-analysis).

Method provenance: directional intensity fractions originate in [Manders et al. 1993](#ref-manders1993), while automatic paired-threshold methodology is described in [Costes et al. 2004](#ref-costes2004). These citations do not imply identical software implementations. In the tested Coloc 2 version, its `Above` predicate includes equality at a positive threshold; OrganelleScope uses strict `>`. [The independent threshold benchmark](docs/validation/COLOC2_THRESHOLD_BENCHMARK.json) retains unaligned differences and separately compares equivalent strict predicates using DoubleType next-representable thresholds. It covers manual boundaries, not automatic threshold-search parity or Costes randomization. Interpretation guidance is given by [Dunn et al.](#ref-dunn2011), [Bolte & Cordelières](#ref-bolte2006) and [Zinchuk & Grossenbacher-Zinchuk](#ref-zinchuk2011).

### 24. Undefined values

Correlation requires nonzero variance in both channels. A constant channel, including a channel that is entirely zero in the ROI, makes Pearson/Spearman undefined. MOC needs a nonzero intensity norm. Directional Manders needs a nonzero sum of its numerator channel. Thus A/B can have M1 = 0 while M2 is unavailable when B is all zero and A is not. A missing value is not a correlation or overlap of zero. Hover/read the supplied reason and inspect channel summaries, source mapping and the selected region.

### 25. Regression, MLE and the coefficient ratio

For the selected target, the engine standardizes nonconstant channel values to mean zero and SD one and fits ordinary least squares using the other nonconstant channels. A signed standardized beta describes conditional linear association within the ROI. It is neither an abundance ratio nor a mechanistic interaction strength. `R²` describes how much target variation the fitted linear combination accounts for in that same ROI; it is not a held-out predictive validation score.

OLS coefficients are also maximum likelihood estimates under an assumed independent equal-variance Gaussian residual model. That mathematical equivalence does not make spatially dependent microscopy pixels independent. No general calibrated standard errors or causal claims are provided. Highly collinear candidate channels suppress individual betas and their ratio because they cannot be reliably separated. The reported coefficient ratio is the largest divided by second-largest absolute beta when defined. It loses sign information and is not a ratio of molecules.

### 26. Descriptive Gaussian likelihood-ratio statistic

The optional reported statistic `−N log(1−r²)` compares unrestricted bivariate Gaussian covariance to zero covariance under an independent-sample model. Perfect correlation is a singular boundary and is unavailable. The app does not assign a calibrated pixel-independent p-value. The null is **zero covariance**, not “no molecular binding.” It is not a posterior probability, Bayes factor or binding likelihood model. Adding a prior cannot turn the wrong biological likelihood into a correct one. See experiment-level inference for the separate Bayesian model actually provided.

---

## Part VII — 3D cuboids, masks and spatial measurements

### 27. Linked sections and cuboid editing

In **3D workspace**, XY, XZ and YZ sections share source-coordinate crosshairs. Choose **Move cuboid** to drag the orange box or click a new location; switch to **Move crosshair** for inspection without relocating the region. Arrow keys move one voxel; Shift plus arrows moves ten. **View cuboid center** moves the section positions to the region; **Place cuboid at crosshair** relocates it. A cuboid spanning an entire axis cannot move along that axis until made smaller.

Edit X/Y/Z start/end bounds or **Width X, Height Y, Depth Z**. Bounds are inclusive, zero-based source indices. A region X 0–63 contains 64 X samples. Resize keeps the center where possible and shifts within source edges. Dashed projected bounds indicate that the current section lies outside the cuboid on its fixed axis; that view is not a slice through the measured region. Z stretch changes section proportions only.

### 28. What cuboid measurement includes

**Measure 3D cuboid** uses all full-resolution source voxels satisfying the selected X, Y and Z bounds, including both end slices, and no voxel outside those bounds in the resulting summaries. Processing, if selected, is performed on the full source XY planes before cropping. The 3D preview's downsampled rays never enter these sums or correlations. A cuboid is limited to 3–500,000 voxels.

Outputs include voxel count, calibrated region volume, per-channel mean/sum/population SD, count above threshold and pairwise correlations/Manders fractions. The UI uses zero Manders thresholds for this workflow. A voxel count of 64 × 64 × 36 is 147,456 selected source voxels; background elsewhere in the stack is not included in that region's summary. These are measurements of a rectangular sampling region, not a segmented mitochondrial/centrosomal volume. Export the 3D report and retain its bounds/recipe. [Implementation](backend/organelle_scope/volume_analysis.py); [independent containment checks](MANUAL.md#28-what-cuboid-measurement-includes).

### 29. Threshold-defined compartment masks

Choose a marker channel and manual threshold or Otsu intensity threshold within the selected cuboid. Otsu separates intensity classes by its histogram criterion; it does not know organelle biology. The foreground rule is strictly above threshold. Connected components separate adjoining foreground; the interface uses six-neighbour connectivity by default (face-sharing voxels). The API also supports higher connectivity settings. Minimum voxel count removes small components. Touching structures may merge; weak structures can fragment.

The **compartment label** is a user annotation. Optional XY ROI edits add/remove mask pixels only on each ROI's recorded Z plane; they are not extruded through depth. Edits outside the cuboid Z range are rejected. Recalculate after editing/excluding object IDs and review the new result before excluding further IDs; labels are identifiers within that segmentation, not persistent cell identities. This is not a learned classifier, watershed package or automatic centrosome detector.

Otsu selects an intensity partition from the supplied distribution; it does not recognize an organelle by protein identity. Uneven illumination, overlapping structures and an inappropriate cuboid can change the mask. Inspect and correct it before biological interpretation. The original algorithm is [Otsu 1979](#ref-otsu1979); broader object-versus-pixel colocalization considerations are discussed by [Lagache et al. 2015](#ref-lagache2015). That paper's methods are not all implemented here.

### 30. Object outputs and surfaces

Each retained object can report label, voxel count, calibrated volume, global centroid in Z/Y/X source coordinates, physical centroid when spacing is known, principal RMS extents, per-channel mean/sum and cuboid-boundary contact. A principal RMS extent comes from the square root of a coordinate-covariance eigenvalue; it is not a full axis length or FWHM. An object touching a cuboid edge may be cut; its measured volume can underrepresent the whole structure.

A marching-cubes mesh can be overlaid in orange on the raw volume. It visualizes the threshold mask; it is not a measured biological membrane or recovered nanoscale surface. Rendering can close cut edges for display. Mesh output is bounded to 50,000 vertices and 100,000 faces; the object budget is 1,000 retained objects. Label export is a ZIP containing cropped uint32 OME label TIFF and measurement JSON. Zero means background; each positive integer identifies an object. Retain the source cuboid origin in JSON to place the cropped labels back in the full stack. [Segmentation implementation](backend/organelle_scope/segmentation.py).

### 31. Image-based proximity and conditional fractions

Choose a different reference channel and its threshold. With XYZ calibration and nonempty marker/reference masks, a distance transform finds the nearest reference foreground voxel center for every marker foreground voxel within the cuboid. Reports show **Marker → reference** and **Reference → marker** separately, each with its own source-foreground voxel count, count within `d`, conditional fraction, minimum, median and 95th percentile distance. Marker foreground includes the applied threshold, minimum connected size, exclusions and manual edits; reference foreground uses its own strict intensity threshold without those marker-mask edits or size filters.

The forward fraction estimates `P(D ≤ d | marker foreground)` **over the selected foreground samples**. It is a conditional empirical spatial fraction, not a posterior probability of binding, a molecular center distance or a voxel-independent significance test. Overlap gives distance zero even when labels correspond to distinct unresolved structures. Truncating the reference at cuboid edges can miss nearer reference signal outside that region. These distances do not model PSF, channel registration or fluorophore/linker offsets. [SciPy calibrated Euclidean distance transform](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.distance_transform_edt.html).

The reverse fraction conditions on reference foreground instead. Fractions weight each source voxel equally, rather than weighting by intensity or treating each connected object as one observation. Reversing direction can change the denominator and summary, but equal values are possible. A zero nearest distance denotes coincident foreground voxel centres; it does not establish molecular contact. Empty masks yield unavailable distances/fractions rather than zero. An empty mask in a crop does not establish protein absence from the cell.

Distances use separate Z, Y and X sampling in micrometres. No isotropic-pixel assumption or surface-to-surface correction is applied. The 95th percentile describes the distribution across source foreground voxels; it is not a confidence interval. Cuboid-face voxel counts report boundary contact and do not correct for omitted structures. Expand the cuboid and vary justified thresholds to assess sensitivity. Saved older reports retain their original forward summary; recalculation supplies both directions. [Dunn et al. 2011](#ref-dunn2011) explains why fluorescence distributions must be distinguished from molecular interactions. The [exhaustive numerical comparison](docs/validation/PROXIMITY_ORACLE_1.0.2.json) covers synthetic geometries and anisotropic sampling, rather than biological specificity.

### 32. Radial enrichment

Optional spherical shells are centered on the selected foreground centroid; an explicit source-coordinate center is also available through the API. Choose radial bin width and outer radius, at most 200 bins. Distances use physical XYZ spacing. Only shell voxels inside the cuboid contribute; shells cut by the cuboid are not extrapolated to full spheres.

For each channel/shell, the engine reports voxel count, sampled physical volume, mean intensity and enrichment `shell mean / whole-cuboid mean`. Enrichment one matches the cuboid average; two is twice that average under this normalization. Neither establishes significance or specific binding. Empty shells and zero denominators yield unavailable values. Changing the cuboid changes the denominator and sampled shell coverage, even with identical signal near the center.

---

## Part VIII — Validation and experimental comparisons

### 33. Numerical reference checks

**Validation** exposes deterministic checks against SciPy correlation functions and hand-derived examples. Passing confirms selected numerical cases, not acquisition quality or biological truth. A separate recorded Coloc 2 comparison covers 12 fixtures and Pearson, Spearman with ties and zero-threshold Manders with a stated numerical tolerance. It does not validate every Costes threshold, randomization test, JaCoP variant or real biological dataset. [Benchmark record](docs/validation/COLOC2_BENCHMARK.json); [validation status](docs/VALIDATION.md).

### 34. Processing sensitivity

Use the same source ROI and zero/manual thresholds to compare raw and prepared intensities. The report supplies each result and processed-minus-raw metric deltas. Automatic threshold mode is excluded from this matched comparison because changing thresholds simultaneously would confound the processing effect. Sensitivity is descriptive: it does not choose the scientifically correct recipe automatically. A small delta under one recipe is not universal robustness.

### 35. Whole-plane spatial shift control

The optional control keeps one ROI and channel A fixed and translates channel B over the **entire XY plane**, wrapping at edges. It computes an upper-tail positive-association Pearson comparison. This preserves the shifted channel's spatial arrangement on a torus; it does not independently shuffle pixels. The user must judge whether translation invariance across the field is defensible. Cell borders, organelle compartments, gradients and ROI selection based on visible overlap can violate this null.

The result includes observed Pearson, null scores/quantiles, exceedances, seed, actual shift count and `(exceedances + 1)/(shifts + 1)` tail probability. Small fields can enumerate all nonidentity shifts; otherwise the engine samples with replacement. Undefined translated correlations cause an explicit error. Limits are 19–999 requested shifts and 25 million selected-pixel comparisons. This is one unadjusted conditional test. Repeated ROIs or channel pairs need a defined multiplicity family; it is not a binding probability, a biological replicate test or Fiji Costes randomization parity. [Spatial-control implementation](backend/organelle_scope/spatial_validation.py).

### 36. Organizing biological units

For experiment comparison, a completed batch must identify **condition**, **independent experiment** and **cell** for every selected image. Multiple ROIs from one cell are averaged, cells are averaged within experiment and independent experiment means receive equal weight. Images with the same condition/experiment/cell IDs are grouped as the same cell. Mislabelled IDs can therefore change the biological unit.

The operational minimum is three independent experiments per condition, not a recommendation that three is sufficient. More pixels/ROIs do not replace independent experiments. Selected measurements must be defined; failed/cancelled images are not silently dropped. Processing and threshold conventions must match. Two to five conditions can be compared for one selected metric and channel/pair. Bounds include 50,000 ROI values, 100 experiments per condition and a bounded resampled-cell work budget.

The app also checks that the selected marker names match exactly across batch images in the same native channel positions. A matching index alone is insufficient. Missing names or a changed selected marker stops the comparison; reconcile channel identities and recalculate first. Matching names are a necessary bookkeeping check, not independent confirmation that labelling is biologically correct.

The experimental unit follows the independently applied intervention and design, rather than the number of observations a microscope produces. [Lazic et al. 2018](#ref-lazic2018) discuss cell-culture examples; [Hurlbert 1984](#ref-hurlbert1984) describes the general pseudoreplication problem. OrganelleScope's experiment/cell hierarchy is a supported design, not an automatic determination of which unit was randomized in your experiment.

### 37. Paired versus independent design

Use **paired experiments** when conditions belong to matched experimental units and their experiment IDs match exactly. Cell counts can differ; the design pairs experiment means, not individual cells. Use **independent experiments** for independent units with distinct IDs across conditions. The engine rejects unmatched pairing and overlapping IDs in an independent design rather than deleting inconvenient units. The correct design comes from the experiment, not whichever test gives a smaller p-value.

### 38. Bootstrap, permutation and multiple comparisons

The hierarchical percentile bootstrap resamples experiments and then cells; paired resampling retains experiment pairing. The reported B-minus-A interval is nominally 95%, on the chosen analysis scale. Percentile intervals can under-cover with few experiments. A local synthetic nested Gaussian study observed coverage below 95%; it is not a universal calibration result. [Simulation record](docs/validation/HIERARCHICAL_SYNTHETIC_BENCHMARK.json).

The two-sided permutation test exchanges independent experiment assignments or swaps matched condition labels according to the chosen design. The result records exact versus randomized enumeration, possible assignments, seed and attainable p-value resolution. With few experiments, p ≤ 0.05 can be impossible even for a strongly separated result. Additional ROIs cannot improve that assignment resolution.

Benjamini–Hochberg adjusted p-values cover all condition contrasts **for this single metric in this report**. They do not automatically include other channels, metrics, exploratory ROIs or other reports. The method targets a false-discovery criterion under its assumptions; an adjusted value is not the chance that a particular null is true. See [SciPy permutation documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html) and the exact [inference code](backend/organelle_scope/experiments.py).

The bootstrap concept is introduced in [Efron 1979](#ref-efron1979). OrganelleScope resamples its declared hierarchy; that extension still depends on the experimental design and sufficient independent units. The classic paper does not validate this application's interval coverage. Use the recorded simulation reports and inspect the design-specific assumptions.

### 39. Fisher transformation, Gaussian MLE and Bayesian uncertainty

For correlations, **Fisher z** is `atanh(r)` and is rejected at ±1 instead of silently clipping. Differences on Fisher-z scale are not direct correlation-unit differences. Mean intensities can use their native scale; bounded fractions/native correlations use descriptive/resampling results. The optional Gaussian model is restricted to intensity means or Fisher-transformed correlations.

Under independent experiment means `x_j ~ Normal(mu, sigma²)`, MLE mu is their arithmetic mean and MLE sigma uses population denominator n. This is separate from ROI regression MLE and the descriptive pixel covariance likelihood ratio. A likelihood describes compatibility with data under parameters/model; it is not a probability of those parameters without a prior.

The Bayesian model uses a Normal–inverse-Gamma prior with visible `mu0`, `kappa0`, `alpha0`, `beta0`. Kappa controls prior precision for the mean relative to variance; alpha/beta describe the variance prior, and beta has squared analysis units. The marginal posterior for mu is Student-t. The report distinguishes posterior mean, 95% credible interval, expected sigma² and posterior variance of mu, and shows sensitivity to beta multiplied by 0.1 and 10. The illustrative default prior is not a validated biological prior.

For reproducibility, let `n` be the number of experiment means, `xbar` their mean and `S = sum((x_j − xbar)^2)`. The implemented update is:

- `kappa_n = kappa0 + n`
- `mu_n = (kappa0 mu0 + n xbar) / kappa_n`
- `alpha_n = alpha0 + n/2`
- `beta_n = beta0 + S/2 + kappa0 n (xbar − mu0)^2 / (2 kappa_n)`
- Posterior mean distribution: Student-t with `2 alpha_n` degrees of freedom, location `mu_n` and scale `sqrt(beta_n / (alpha_n kappa_n))`.
- Expected variance `E[sigma² | data] = beta_n / (alpha_n − 1)`; posterior variance of the mean is `beta_n / ((alpha_n − 1) kappa_n)`.

These equations describe the recorded Normal–inverse-Gamma convention. Rescaling intensities changes variance units and requires reconsidering beta; copying a prior between instruments/scales is not automatically meaningful.

Bayes' theorem combines likelihood and prior and normalizes to a posterior. A credible interval is conditional on that model/prior; it is not a guarantee of 95% repeated-sampling coverage. The descriptive normality check does not establish normality when nonsignificant. Check outliers, experiment means, pairing, variance and prior sensitivity. No current Bayesian model estimates molecular-binding probability or predicts a knockdown mechanism from colocalization.

---

## Part IX — Batch analysis and Excel

### 40. Manual per-image review

Upload up to 50 TIFFs in **Batch analysis**. Each image has independent axes/calibration, ROIs, threshold/target choices and preparation settings. Select a queue item, inspect a Z plane and draw/resize its circles or polygons. Physical-circle placement accepts a diameter in µm (initial entry 2 µm), not radius. No ROI template is forced onto all images, no LLM learns morphology and no automatic ROI drawing is implemented.

Optional condition, experiment and cell labels support later aggregation. **Experimental design review** lists image counts, labelled experiments and nested cell IDs per condition, missing design labels and repeated raw-source hashes. Counts describe supplied labels; they do not verify independence. Missing design labels allow descriptive image measurements. Identical raw sources assigned to different conditions or experiments are rejected by experiment inference. File copies do not create replicates. The frozen run and Excel **Design review** sheet preserve these checks. Open **Confirm channel identities and inspect signal** beside each batch image to edit stored-channel names and inspect the selected plane. Applying new names preserves drawn ROIs and clears review. Changes to source metadata after saving also invalidate review on the backend; earlier frozen runs retain their original labels as historical records and require a new run for corrected interpretation. Check **I reviewed the ROIs, calibration, channel mapping and settings for this image** for each item. Measurement-affecting changes clear its review. Failed imports remain explicit; a file that did not import is not an analysed negative result. Save the batch separately from a single-image project.

### 41. Running, cancelling and reopening

**Analyze reviewed batch** saves and freezes a revision into a separate run. If another workspace changed image calibration, review affected items again. Runs are sequential and retain per-image status. Cooperative cancellation is checked between bounded operations; an operation already running can take time to return. Completed results survive cancellation. Restart marks unfinished work interrupted and does not silently resume it.

A later batch edit cannot rewrite an earlier frozen run. Select an earlier run to export it again. Removing a queue item does not delete the source microscopy data or saved run. Batch sessions are manual-save records; keep the saved batch/run as well as exported files. [Detailed batch methods](MANUAL.md#part-ix--batch-analysis-and-excel).

### 42. Excel workbook contents

| Sheet | Contents |
|---|---|
| Read me | Scope, conventions and interpretation notes |
| Images | Per-image identity, labels, status/failure and provenance |
| Settings | Calibration, source/processing/threshold choices and engine details |
| ROI geometry | Region IDs, vertices, plane and physical diameters |
| Colocalization | Pairwise metrics per region/image |
| Intensities | Per-channel regional summaries |
| Regression | Target, coefficients, fit summaries and warnings |

Values are numeric where defined; unavailable measurements are blank, not zero. User strings are literal, including strings starting with `=`. The workbook has no formulas or external links and requires no Excel/cloud API to generate. Excel uses one-based plane/channel presentation where documented; JSON preserves native zero-based indices and nested provenance. Limits include two million cells, Excel's row limit and 32,767 characters per cell. Errors replace silent truncation; split a large export or preserve full JSON. Excel/Numbers rendering and native desktop download behaviour require platform qualification beyond valid OOXML generation.

---

## Part X — STRING, KEGG and pathway diagrams

### 43. Database queries and privacy

The current integration supports human identifiers: taxonomy 9606 for STRING and `hsa` for KEGG. No API key is needed for the selected public mapping/network/find/link/list endpoints. Lookups need internet unless an exact suitable cache record exists. Only identifiers/species and public lookup parameters are sent. Images, local measurements and assistant conversations are not supplied to these databases. Local-model inference is independent of online lookup permission.

Candidate symbols can be ambiguous. Explicitly select the correct gene/protein before requesting a network or pathway memberships. A familiar alias is not proof of an exact match. Database content can change: retain retrieved identifiers, versions, URLs, dates and hashes. API errors are reported rather than replaced with invented model evidence. See [STRING API](https://string-db.org/help/api/) and [KEGG REST](https://www.kegg.jp/kegg/rest/).

### 44. STRING interpretation

Choose functional or physical association mode and the minimum score. The implementation queries selected proteins without silently adding neighbouring nodes; STRING is pinned to the documented version 12.5 endpoint. Request thresholds use a 0–1000 scale; response scores use 0–1. Component evidence scores are shown when returned. A “physical” association record is still database evidence, not an experiment-specific proof of direct binding.

An association score is not `P(binding | this microscopy ROI)`. Network edges may reflect different evidence types and biological contexts. Lack of a returned edge can reflect thresholding, mapping or incomplete evidence rather than absence of interaction. No STRING database dump is bundled. [Provider documentation and access terms](https://string-db.org/help/api/); [application evidence methods](MANUAL.md#part-x--string-kegg-and-pathway-diagrams).

### 45. KEGG pathways and diagrams

Select KEGG, acknowledge academic research use, enter a human symbol and explicitly select a gene. Retrieve pathway memberships; **View diagram** opens an official PNG in a zoomable/scrollable dialog with source links and retrieval/cache provenance. The interactive provider map remains a separate link. A membership list is not enrichment analysis. A coloured reference map is not an experimentally inferred activation map or a validated silencing simulation.

No whole KEGG package is installed. The app caches a small pathway-name catalogue and explicitly requested evidence/maps. Lookup output is bounded to 25 candidates/pathways; names are resolved for the first ten pathway entries while remaining IDs can remain available. Failures, missing maps and stale cache are visible. No substitute diagram is generated by the LLM. KEGG access is constrained to the academic-use workflow; do not assume the application's own eventual license grants database redistribution/commercial rights. [KEGG API terms](https://www.kegg.jp/kegg/rest/); [API operations](https://www.kegg.jp/kegg/rest/keggapi.html).

### 46. Cache and offline mode

The evidence cache is bounded to 64 entries/64 MiB, with a seven-day freshness window. Offline-only uses the exact cached query, labels stale records and fails clearly on a cache miss. Text responses are capped at 1 MiB; map PNGs at 4 MiB and 16 megapixels. HTTPS verification uses certifi CA roots. Calls are serialized with at least 1.05 seconds between starts. Content hashes are checked before cached reuse. These are engineering limits, not guarantees that the provider is always reachable.

Cache files are not a permanent scientific archive: export/save the query evidence and provenance needed for the study. Project evidence records retain source metadata; diagram pixels live in the bounded cache and may need refetching. A current positive live lookup does not establish indefinite provider availability or the validity of a biological conclusion.

---

## Part XI — Local assistant and model decisions

### 47. What the assistant can do

The optional local interpretation model is **Gemma 4 12B Instruct, official QAT Q4_0**, through the pinned local llama.cpp runtime. It can answer general microscopy/method questions without an image or saved project, inspect a question-time workspace snapshot including unsaved settings, read recorded measurements/evidence, request deterministic reference checks and optionally repeat the exact selected evidence query. Tool records and verified source links accompany the answer. It cannot run arbitrary code, edit ROIs or silently change analysis settings.

Ask requires a nonblank question and no request already running in that panel. A missing model/runtime is a setup error, not a requirement to save a project. Ready can be reached automatically when installed runtime/model files are valid. Images/measurement data and conversations stay local in the current assistant path. Optional online evidence refresh sends identifiers only and remains subject to database academic/offline settings. No Firebase, hosted LLM service or Streamlit account is required for the desktop app.

The assistant now receives an application-generated reading guide before answering: matching cuboid, segmentation, selected-plane quality and experiment summaries, plus selected cached STRING/KEGG evidence even when it does not choose an evidence tool. It still receives no microscopy pixels. Per-image reports are excluded when source hash or image metadata differ. Experiment summaries must match the selected batch and are explicitly separate from the current-image findings. Summaries may be bounded; the full exported report remains authoritative. These are supplied application reports, not an independent remeasurement by the LLM.


#### Model setup and operating limits

The pinned model is `gemma-4-12b-it-qat-q4_0.gguf`, 6,975,879,296 bytes (6.98 GB / 6.50 GiB), from [Google's official QAT repository](https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf), revision `29d097773436b69ff9feafd636ab4cf873786537`. SHA-256: `93567e57a8fe10b23569b9d9ec38cd005deedf71e29477c421a4b83f418a538b`. The runtime is [llama.cpp b11669](https://github.com/ggml-org/llama.cpp/releases/tag/b11669). Upstream full-precision benchmark claims do not establish performance of this quantization in microscopy.

The application uses an 8,192-token context, one request at a time, up to four model-selected read-only tool calls, temperature 1.0, top-p 0.95 and top-k 64. Thinking is disabled; no internal reasoning is saved. The answer budget is 1,600 tokens (1,200 for a validation rewrite); the question limit is three hundred words. Asking can start a valid installed model and wait up to two minutes for readiness. **Unload model** releases its owned process; normal backend shutdown also stops it. The loopback runtime uses a random port/session secret and does not accept arbitrary remote inference endpoints.

Leave at least about 7.5 GB of free disk space for model setup, plus space for images. At least 16 GB RAM is recommended; the development target is M3/24 GB. Weight size is not total memory: context, libraries and image stacks also consume memory. These are engineering recommendations, not a guarantee on every machine. Setup progress/pause/resume is separate from asking a question; asking does not bypass missing files or checksum errors.

The assistant has no shell, arbitrary filesystem/URL, image-editing or setting-write tool. Online refresh can only repeat the exact selected evidence query under its existing permissions; it cannot choose a new protein query or URL. PubMed retrieval, assistant-opened diagrams, automatically applied recipes and new agent-run measurements are not implemented. The question-time context is capped at 16 MiB. Invalid source identifiers, model-provided URLs and generated numeric measurement prose are checked; one restricted rewrite may be attempted. Exact recorded marker/ROI and gene identifiers may contain digits. These syntactic checks cannot validate every qualitative statement.

For explicit source setup, run `backend/.venv/bin/python scripts/setup-local-assistant.py --download` (Windows: `backend\.venv\Scripts\python.exe`). Without `--download`, the script prints the manifest. Source checkouts do not download automatically. Runtime/weights are stored in ignored `.local-runtime/` and `.local-models/`; overrides `ORGANELLESCOPE_LLAMA_SERVER` and `ORGANELLESCOPE_MODEL` still require pinned integrity. Installed builds manage storage separately and need no Python or Ollama installation. For reproducible candidate assessment, `scripts/setup-local-assistant.py --candidate liquid --download` and `scripts/evaluate-local-assistant.py --model gemma` or `--model liquid` use named development fixtures and a local output path; they do not change the application's selected model. Retain one active model and small evaluation records; remove identified superseded staging only, preserving research data and required notices.

#### Recorded summaries and unavailable AI drafts

**Show recorded analysis summary** uses the calculation engine and application reading guide without loading Gemma. It works without a saved project and without downloaded weights. It displays current, provenance-matched quantities and notes; it is not a generated answer to arbitrary questions. When a model draft fails application checks or a generation request fails after model startup, the chat returns a clearly labelled application summary, preserves the attempted tool record and keeps the question for retry. Missing model/runtime setup remains an explicit setup error. No failed draft is silently relabelled as a supported finding.

For matching 3D proximity reports, **Recorded analysis · application findings** appears separately above the generated draft. These statements are assembled from report status and scope, including unavailable empty-mask results and the fact that both directions are already calculated. They remain separate from the model's prose and its automatic claim review. Recorded quantities preserve numerical values and units; concise AI answers may omit context, even after quotation checks. The [assessment review](docs/validation/ASSISTANT_PROXIMITY_REVIEW_1.0.2.json) records examples and the scope of the follow-up.

### 48. How to read an answer

Current releases add an automatic claim-to-source review after generation. The reviewer receives the actual cited records and must distinguish record-supported findings, general knowledge, advice, hypotheses and unsupported statements. Factual claims require source quotations that match the supplied text. Conservative topic checks reject quotations missing critical concepts in the claim; additional scope checks reject unqualified binding/activation/causality claims. These checks can still accept irrelevant or misleadingly interpreted quotations and can withhold valid paraphrases. The UI exposes reviewed sentences, quotations and review status. Statements flagged by these checks are removed from the displayed draft; unsupported claims can still escape the checks, and valid statements can be withheld. Supported or explicitly labelled methodological statements may remain. If none survive, the application shows a fixed explanation and the deterministic report notes. Unqualified statements treating corrected channel labels as biological ground truth are withheld; an owner correction is an annotation, not independent identity verification. Duplicate advice/hypothesis prefixes are normalized for readability. Marker-specific Manders direction/magnitude statements from the model are omitted: the engine supplies the actual marker order in M1/M2 definitions and recorded-quantity labels. This avoids relying on the model to translate A/B into biological marker names. Unknown or unsupported references remain withheld. This is the same local model reviewing its own draft: correlated errors and irrelevant-but-matching quotations remain possible. Passing this check does not prove citation entailment, authenticate an edited cached record, or establish biological truth. Uncited factual explanations are withheld. Clearly labelled advice and hypotheses may remain, and must not be presented as measured findings. They still require scientific review.


The assistant's qualitative draft is distinct from engine-derived numbers, which the app presents separately. Citation checks, tool allowlists, source hashes, exact-identifier handling and numeric-prose guards reduce some failures, but do not verify all scientific statements. The model can overstate a control's necessity, confuse a statistical model or infer unsupported directional pathway effects. A cited source can be real yet not support every sentence. Review source-claim agreement and label measured findings, methodological advice and hypotheses separately.

No saved documentation of a control is not proof that the control was never performed. A suggested experiment has not been run simply because the assistant mentions it. Hypothetical knockdown reasoning should state assumptions and alternatives; it is not a measured or calibrated causal prediction. The bounded tool loop allows at most four tool calls and qualitative response checks; it is not an autonomous wet-lab agent. [Observed Gemma failures](README_MODEL_DECISIONS.md#preserved-assessment-gemma-evaluation); [assistant operation](#47-what-the-assistant-can-do).

Each new answer includes expandable **Measurement context · application checks**. These deterministic notes are generated from report scope and settings independently of model prose. They identify missing calibration, constant channels, zero-threshold overlap, boundary limitations, batch scope and the distinction between database context and measured activation. The assistant should answer the actual question first, separate observations, explanations, advice and hypotheses, and propose a check that can distinguish alternatives. These notes do not certify that every generated sentence is correct.

For example, a threshold mask's high conditional proximity fraction can support an image-scale spatial description. It cannot establish molecular binding. A constant-channel correlation is undefined despite a completed calculation; changing a threshold does not restore missing variation. KEGG membership can motivate a hypothesis for knockdown studies, but does not establish that a pathway was active or predict a causal direction in the imaged cells. Review measurement interpretation against [Dunn et al.](#ref-dunn2011), acquisition limitations against [Jost & Waters](#ref-jost2019), and replicate claims against [Lazic et al.](#ref-lazic2018).

Local generation can take minutes on a CPU or a busy computer. Each completion request has a five-minute timeout; a timeout is an operational failure and is not evidence for an answer. The synthetic assessment records both accepted drafts and timeouts. See [current interpretation/QC verification](docs/VALIDATION.md) and [qualitative model review](README_MODEL_DECISIONS.md#preserved-assessment-assistant-interpretation-review).

### 49. One model, vision options and GPT-OSS

If one model is selected today, keep Gemma because its integration has been assessed locally. This is not proof it is universally superior. Google describes the upstream Gemma 4 12B as multimodal; **our application currently uses text only**, without sending microscopy pixels. Its existing GGUF/runtime image path needs separate qualification. Previous shorthand calling it a text-only model referred to this deployed use, not upstream capability. [Google model card](https://huggingface.co/google/gemma-4-12B-it).

Llama 3.2 Vision 11B **could replace Gemma**, after adapting model loading, prompt/image formatting and tools and passing an application trial. It is not a drop-in weight swap and is not currently recommended as an evidence-backed improvement. Qwen2-VL-7B is a candidate for image questions, not the same model as the earlier retired Qwen3.5-4B text profile. Optional image support and a two-model design remain proposals, not current features. The [model selection assessment](README_MODEL_DECISIONS.md#preserved-assessment-model-selection) records MicroVQA results, LLaVA-Med deployment concerns, Pixtral and the BioVLM naming ambiguity.

GPT-OSS-20B is a text/tool-use challenger, not a vision upgrade; GPT-OSS-120B is outside the current 24 GB target. Official documentation's approximately 16 GB MXFP4 GPU guidance for 20B is precision/hardware-specific, not a guarantee on an M3 alongside image rendering. Harmony formatting needs qualification. Neither GPT-OSS candidate has been downloaded or locally compared. No benchmark-based claim of superior microscopy interpretation is made. [OpenAI model documentation](https://developers.openai.com/api/docs/models/gpt-oss-20b); [hardware guide](https://developers.openai.com/cookbook/articles/gpt-oss/run-transformers).

The [cumulative model decision record](README_MODEL_DECISIONS.md) preserves prior Qwen, Ministral, Gemma and Liquid assessments. Retain only chosen active weights/runtime; optional candidates should not inflate the default installer or remain on disk after an explicitly completed trial. The current 6.98 GB weight file size is not total runtime memory.

---

## Part XII — Projects, exports and reproducibility

### 50. Projects and recovery

A project contains one imported image association or an evidence-only workspace. **Save project** updates the current record with a revision check; **Save as new** creates another. Opening/importing a different project can replace unsaved workspace state, so review the prompt. Saved snapshots retain calibration, ROIs, recipes, thresholds, measurements, workspace reports/evidence and recent conversation state. Some transient state—unfinished gestures/dialogs/running jobs—is not a project record. Not every camera gesture is guaranteed to restore on a new application session; camera preservation when switching tabs is a different behaviour.

The app verifies source SHA-256 and import metadata on reopening. Shared-source calibration changes can require an isolated association rather than rewriting another project's analysis. Project metadata/reports are capped at 16 MiB. The selector lists the fifty most recent projects; older files remain on disk. The separate latest-workspace recovery slot autosaves after idle time, but is not a multi-revision backup. Restore is explicit. A new workspace can replace that slot; manually save important states.

### 51. Portable archives and legacy preservation

Exporting a portable project archive exports the **saved revision**, not arbitrary unapplied edits. ZIP archives include source TIFF, project/settings/reports and referenced historical numeric artifacts when applicable. Import validates paths, duplicate/oversized contents, source metadata/hashes and creates new identifiers. This is separate from a batch workbook. Always test reopening an important archive before deleting an external backup.

Historical denoising/deconvolution reports and artifacts remain preserved as records. Opening such a project makes an unsaved recalculation copy using supported source/background/smoothing settings and clears stale derived reports in that copy. The original saved report remains unchanged. New analyses reject retired restoration settings rather than silently substituting raw data. Historical recovery states are preserved before replacement. Do not interpret an old restoration record as an active current processing option.

### 52. Export guide

| Export | Best use | Does not replace |
|---|---|---|
| Inspection JSON | Source info, current selected plane/ROIs/profile/analysis, LUTs and preparation recipe | Original TIFF and a complete portable project |
| ROI/validation/3D/experiment JSON | Exact requests, metrics, warnings and provenance for that workflow | Independent biological validation |
| Snapshot PNG + details JSON | Present the selected XY plane or volume camera, with display provenance | Native channel data or full source resolution |
| Mask ZIP | Cropped label TIFF and measurement JSON with source origin | Uncropped source acquisition |
| Batch Excel + full JSON | Tabular review and full nested per-image results | Batch session source files and experiment design records |
| Project ZIP | Transport a saved one-image workspace and associated source/artifacts | All application data or every batch run |
| Evidence JSON | Provider query/results, retrieved IDs, URLs, timestamps/hashes | A redistributed full database or a causal pathway model |

### 53. Local storage and backups

Development stores include `.dev-images/`, project/evidence/assistant data directories and managed local model/runtime folders. The desktop image service uses the application's Electron user-data images directory; related application records live in its managed storage. Exact parent locations depend on platform/build. Back up the full managed research-data set, not only project JSON. Original import copies and saved batch runs are research records, not disposable cache.

A source SHA-256 detects byte differences; it is not encryption, a biological validity score or a complete chain of custody. Reports should retain source hash, image metadata, exact ROI/bounds, processing/threshold conventions, algorithm version, seed, experiment labels and evidence provenance. A screenshot of a result table is insufficient for reproduction. Removing superseded generated installers is different from deleting source images, ROIs, conversations or evidence exports.

---

## Part XIII — Troubleshooting and responsible interpretation

#### Startup diagnostics and upgrades

The installed app writes bounded `logs/startup.jsonl` diagnostics under its application data folder: normally `~/Library/Application Support/OrganelleScope` on macOS and `%APPDATA%/OrganelleScope` on Windows. One rotated file is retained; startup records omit images, question text and measurement reports, and redact the application session secret. Logs stay local. They record authenticated backend readiness, renderer/preload failures, owned-backend exit and shutdown. Startup errors identify the log location. Diagnostic storage failures do not prevent analysis startup. Review any excerpt before manually sharing a bug report.

Readiness checks use an authenticated session endpoint, rather than accepting any HTTP response on the selected port. Normal application quit waits for the owned backend; forced termination is bounded. Windows termination targets only the owned process tree. This does not promise cleanup during an operating-system crash or forced machine shutdown. These lifecycle choices use Electron's documented [before-quit](https://www.electronjs.org/docs/latest/api/app#event-before-quit) and [renderer-process-gone](https://www.electronjs.org/docs/latest/api/web-contents#event-render-process-gone) events.

Save/export important work before an upgrade, quit the application, then replace the application binary with the verified release. Data/model storage is separate from the installer; a valid existing Gemma file is reused. No source-image or project migration is introduced by 1.0. Previous installers remain in GitHub Releases for rollback. Report problems through GitHub Issues with the exact version/platform and reproducible steps, preferably using a synthetic or explicitly shareable example.

### 54. Common symptoms

| Symptom | First checks |
|---|---|
| Preview unavailable | Confirm supported dtype, static axes and series; inspect import error rather than guessing Z/C |
| Wrong colours | Check each channel LUT and actual marker labels; RGB components may be a composite export |
| A channel has no signal | Inspect its regional mean/sum/SD and a larger source area; verify channel mapping and ROI plane |
| Correlation unavailable | Look for constant/zero channel, too few samples or an invalid denominator |
| High Manders, low Pearson | Positive pixels overlap while intensities do not covary; inspect thresholds/background |
| Preparation looks unchanged | Apply the recipe; inspect offsets/sigma, background/residual and numeric changes |
| ROI draws while trying to move image | Enable Pan image or use Space/middle drag; disable it again for drawing |
| Cuboid will not move | Reduce size along any fully spanned axis; inspect valid inclusive bounds/interaction mode |
| Cuboid projection is dashed | The current section is outside the region on the fixed axis; use View cuboid center |
| 3D looks flat/empty | Inspect linked sections, true Z extent, opacity/cutoff, calibration and voxel-space warning |
| Apparent object changes after threshold | Connected-component topology depends on threshold, minimum size and edits; review again |
| Cannot compare experiments | Check completed statuses, nonempty labels, matched recipes and valid paired/independent IDs |
| Bayesian output unavailable | Use intensity mean or Fisher-transformed correlation; review prior/domain constraints |
| KEGG/STRING unavailable | Check exact identifier, provider status, academic acknowledgement and offline/cache mode |
| Assistant unavailable | Check model/runtime setup, integrity and resource availability; saving is optional |
| Export too large | Split the job or preserve JSON; do not silently truncate the record |
| Imported legacy project lacks new analysis | It is a preserved historical result with a separate recalculation copy; recalculate supported inputs |

### 55. Worked interpretation examples

**Example A: High M1 but low Pearson.** If most A intensity lies at positive B pixels, M1 can be high even when the intensity values do not track one another. This supports that particular co-occurrence description under the recorded threshold. It does not identify a stoichiometric complex. Compare background/threshold sensitivity and independently justified regions.

**Example B: Empty third channel.** Suppose A and B vary, while C is all zero inside a cuboid. A/B correlation can be defined, A/C correlation is undefined, A/C M1 can be zero and its reverse fraction unavailable. These outputs are mathematically consistent; inspect whether C is a genuine blank channel, wrong mapping or absent in that region.

**Example C: Knockdown comparison.** A difference between independent experiment means is a measured condition association under the design. A treatment may have off-target effects or change morphology/background. A KEGG pathway containing the target adds context but does not identify the direction of a downstream response. Distinguish a measured phenotype, a mechanistic hypothesis and the controls needed to discriminate alternatives.

**Example D: Small nearest-mask distance.** A value below the diffraction-limited PSF scale can arise from voxel geometry or overlapping blur. Metadata-based coordinate conversion does not validate molecular proximity at that precision. Report the measured mask-distance definition and acquisition limits rather than relabelling it a true inter-protein distance.

### 56. Preparing a research report

Record acquisition modality/objective and sampling, raw-channel provenance, registration/PSF information actually available, saturation checks, experimental units and controls, ROI selection criteria, preparation and threshold settings, analysis definitions, excluded/failed records, software/model versions, uncertainty model and multiplicity family. Describe what was not calibrated without inventing numerical uncertainty. Treat synthetic references as numerical evidence only. For strong molecular/causal claims, select additional assays appropriate to the hypothesis with domain expertise; no single suggested assay universally establishes binding or causality.

---

## Part XIV — Development, distribution and comparisons

### 57. Development setup

Source checkout requires compatible Node.js (the project targets 24+) and Python (backend declares 3.11+; CI uses 3.12). Install backend/test requirements in an isolated environment, install root/frontend dependencies and run the dev launcher with the selected Python environment. Do not commit local images, credentials, environments or weights.

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -e 'backend[test]'
npm ci
npm ci --prefix frontend
ORGANELLESCOPE_PYTHON=backend/.venv/bin/python npm run dev
```

The environment-variable/path syntax above is macOS/Linux shell syntax. On Windows, use the environment's Python executable and the corresponding PowerShell variable syntax. The GUI communicates with an authenticated loopback service; its development token is not a credential for an internet deployment. The application is designed for local desktop use, not exposing that service publicly.

Native builds additionally need PyInstaller. `npm run package` builds the UI, freezes the backend, collects dependency notices and packages the host installer into ignored `release/`. Run source assistant setup explicitly if needed.

Relevant checks are `python -m pytest backend/tests -q`, frontend `npm test`, UI production build, frozen-service smoke, platform packaging, signature verification and installer integrity. They establish different properties. Native user acceptance, large-workload behaviour, scientific validation, model interpretation and Apple notarization are not implied by a passing unit suite.

### 58. Installers, GitHub Actions and licensing

Development workflows build Windows x64/macOS ARM64 artifacts and checksums. **GitHub Releases** is the appropriate user-facing place to attach installers; **Actions artifacts** are build outputs with their own retention/access behaviour. **GitHub Packages** is a package/container registry, not the usual DMG/EXE download page. The tagged installer workflow publishes both verified platform builds together after both packaging jobs pass. A tag with a suffix, such as `-rc.1`, is a prerelease; a plain version tag is a stable release and requires complete native startup/runtime/workload reports tied to the installer hashes. Stable startup evidence must include two fresh profiles and one retained-profile launch, with observed backend shutdown. Manual workflow runs retain build artifacts without publishing a release. Local `release/` outputs are ignored by Git and are not uploaded just by pushing source.

For a release, commit consistent application/backend versions and release notes, push tested source, then push a matching version tag (`v1.0.0` for a stable release or a suffixed tag for a candidate). Both native runners run source tests, frozen-service smoke checks, runtime-loading checks, synthetic stack workloads and installer startup checks. Only after both pass does the publishing job create a draft, upload both installers/checksums/notices/reports, verify server digests and publish the qualified release. Failed uploads retain a draft. Inspect assets against the exact tag/checksum; no workflow establishes biological truth. The publish job alone receives GitHub's temporary contents-write token; no publishing token belongs in Git.

`scripts/dependency-notices.py` gathers licence texts for declared runtime requirements, providers in the frozen module graph and dependencies. Build-specific notices in ignored `build/notices/` are bundled and attached to the release. Electron retains Chromium notices; required predecessor/model notices remain in `third_party/`. Retired component notices remain in Git history rather than being redistributed as active dependencies.

Installer version and checksums must match. The currently verified compact installer is separate from later source work. The repository now includes the user-provided [GNU GPLv3 LICENSE](LICENSE). Retained predecessor PolyForm Noncommercial notices and third-party terms remain relevant; the repository license alone does not settle redistribution rights for every component. Public repository visibility does not itself grant unrestricted reuse. Model licenses, provider database terms and application code licenses are distinct. No KEGG/STRING database dump or model weights is committed to this repository.

### 59. Comparison and scope

See the [detailed software comparison](docs/SOFTWARE_COMPARISON.md) for napari, QuPath, CellProfiler, Fiji JaCoP/Coloc 2, Icy and Imaris. Compare actual versions, enabled modules/plugins and matched metric/threshold/mask conventions. This is a workflow comparison, not an accuracy ranking or assertion of unique algorithms.

The application uses established scientific viewing conventions; references to other viewers are comparisons, not claims that their features originated here. No third-party viewer code or dependency was added by these layout changes. The UI uses #6DB1BF for the Workspace/header, #FFEAEC for panels, #FDF0D5 for the page/inputs and #83BCFF for primary/selected controls, with dark readable text. Image LUTs and scientific overlays are independent of this interface theme.

---

## Part XV — Glossary

| Term | Meaning in this manual/application |
|---|---|
| Acquisition | The original microscope recording process and its settings |
| Additive composite | Display made by summing coloured channel contributions, then clipping |
| Algorithm version | Identifier of the implemented calculation convention |
| Alpha / beta prior | Shape/scale parameters of the variance prior; not regression beta |
| Anisotropy | Unequal sampling distances along axes |
| API | Interface used to request data or calculations from a service |
| Area | Number of selected pixel centers times calibrated pixel area |
| Artifact | A generated data object, or an unwanted acquisition effect; context distinguishes them |
| Association | A relationship in observations or reference evidence, without automatic causality |
| Atanh | Inverse hyperbolic tangent used for Fisher-z transformation |
| Axes | Mapping of array dimensions to X/Y/Z/C/T |
| Background | Intensity attributed to non-target signal under a chosen model |
| Batch | Editable queue of independently configured images |
| Batch run | Frozen revision and per-image execution results |
| Bayes' theorem | Rule combining prior and likelihood into a posterior |
| BF16 | Brain floating-point 16-bit numerical representation; different from an 8/16-bit TIFF dtype |
| BH adjustment | Benjamini–Hochberg adjustment for a defined family of comparisons |
| Binding | Molecular interaction requiring evidence beyond image overlap alone |
| Bit depth | Storage precision/range of a recorded value, not spatial resolution |
| Bootstrap | Resampling procedure used to approximate variability under assumptions |
| Boundary flag | Indicator an object touches the selected cuboid edge |
| C / channel | Acquisition signal dimension; not necessarily an RGB display component |
| CA roots | Trusted certificate authorities used to verify HTTPS connections |
| Calibration | Mapping of sample indices to physical distances, with recorded provenance |
| Cell ID | Label grouping measurements attributed to one cell in an experiment |
| Centroid | Mean coordinate of selected object voxel centers |
| Clipping | Limiting values to a range; display clipping differs from numerical subtraction clipping |
| Colocalization | Defined spatial co-occurrence/covariation at an acquisition/analysis scale |
| Collinearity | Candidate signals are too linearly dependent to separate regression effects reliably |
| Compartment | A user-defined or biologically justified region; not automatically identified by its label |
| Condition | Experimental group, such as control or treatment |
| Conditional fraction | Fraction within a defined subset, such as marker foreground |
| Confidence interval | Interval procedure interpreted through repeated-sampling behaviour under assumptions |
| Connected component | Foreground samples linked under the chosen neighbourhood rule |
| Constant channel | Identical values across the selected region; correlations are undefined |
| Contrast ceiling | Intensity mapped to the top of a display range |
| Covariance | Joint centered intensity variation |
| Credible interval | Posterior interval conditional on a model/prior |
| Cuboid | Rectangular XYZ sampling region with inclusive source bounds |
| Cutoff | Rendering visibility control; not automatically a measurement threshold |
| Deconvolution | Inversion of an imaging-blur model; removed from the current feature set |
| Decoded size | Estimated uncompressed array storage; not peak application memory |
| Degrees of freedom | Distribution/model parameter reflecting independent information under assumptions |
| Diameter | Twice radius; physical circle editor uses diameter in µm |
| Distance transform | Distance from each sample to nearest reference foreground under specified geometry |
| Dtype | Numerical storage type, such as uint16 or float32 |
| Effect / contrast | Defined difference, here condition B minus A on the analysis scale |
| Enrichment | A specified normalized intensity ratio, here shell mean divided by cuboid mean |
| Evidence | Supplied provider/measurement record; distinct from model speculation |
| Exact permutation | Enumeration of the allowed assignment set |
| Experiment ID | Label for an independent or matched experimental unit, not one ROI |
| False discovery rate | Expected false-discovery proportion targeted by procedures under their assumptions |
| Fisher z | Atanh transformation of a correlation, undefined at ±1 |
| Float32 | Floating-point representation for corrected intensities, not a new acquisition bit depth |
| Foreground | Samples satisfying the mask/threshold rule |
| FWHM | Full width at half maximum above the profile's estimated baseline |
| Gamma-tubulin / pericentrin | Example biological markers; their identity/specificity is experimental context |
| Gaussian smoothing | Weighted local averaging with a Gaussian kernel |
| GGUF | Local model distribution format used by the current runtime |
| GPU / VRAM | Graphics processor and its memory; Apple unified memory is shared with the rest of the system |
| Hash / SHA-256 | Content fingerprint used to detect byte differences |
| Hierarchical bootstrap | Resampling at multiple defined levels, here experiments then cells |
| Histogram | Distribution of intensity counts used by threshold methods |
| Hypothesis | Proposed explanation requiring suitable evidence/testing |
| Identifiability | Ability to distinguish separate model parameters from the data |
| ImageJ TIFF | TIFF variant with ImageJ metadata conventions |
| Independent replicate | Experimental unit whose independence is justified by study design |
| Integrated intensity | Sum of values over the selected region |
| Interpolation | Estimating values between samples; not acquiring new information |
| KEGG | Reference gene/pathway database queried in the academic workflow |
| Kernel / footprint | Neighbourhood/weight shape used by a filter |
| Label TIFF | Integer image whose positive values identify segmented components |
| Likelihood | Function of parameters describing observed data under a specified model |
| Likelihood ratio | Comparison of two specified likelihood models; not automatically Bayesian evidence |
| Localization precision | Uncertainty of estimated emitter location; not the same as pixel spacing |
| LUT | Lookup table mapping display intensity to colour |
| Manders M1/M2 | Directional intensity fractions under recorded paired thresholds |
| Mask | Boolean or integer spatial selection for analysis |
| Maximum likelihood estimation | Choosing parameters that maximize a specified data likelihood |
| Median | Middle ordered value; distinct from mean and minimum |
| Mesh | Polygonal surface for rendering a threshold boundary |
| Metadata | Stored information about axes, sampling, acquisition and file structure |
| MLLM / VLM | Model accepting visual and language inputs, subject to its integration limits |
| MOC | Uncentered Manders overlap coefficient |
| MoE | Mixture of experts; active computation does not eliminate storage for other experts |
| Morphology | Shape/distribution of a structure; not a verified biological identity |
| Native intensity | Recorded detector value or explicitly defined corrected value, not screenshot RGB |
| Normal–inverse-Gamma | Conjugate prior family for a Gaussian mean and variance |
| Null model | Explicit reference mechanism used for a statistical comparison |
| Numerical validation | Checking computations against known/independent examples |
| OLS | Ordinary least squares regression |
| OME-TIFF | TIFF with Open Microscopy Environment metadata |
| Otsu threshold | Histogram-based class-separation threshold, without biological recognition |
| Paired design | Comparison of genuinely matched experimental units |
| Percentile | Value below which a specified fraction of observations lies |
| Permutation p-value | Tail calculation under allowed label assignments and assumptions |
| Photon count | Physical detector quantity not automatically equal to TIFF gray value |
| Pixel / voxel | Sample in a 2D plane / 3D array, with a recorded spacing |
| Plane | One XY slice at a specified source Z index |
| Posterior | Distribution after combining prior and likelihood |
| Principal RMS extent | Square root of coordinate-covariance eigenvalue; not a full object diameter |
| Prior | Distribution expressing assumptions before the current likelihood update |
| Processing recipe | Recorded sequence/settings defining corrected intensities |
| Projection | Reduction of volume information to a lower-dimensional representation |
| Provenance | Record of source, settings, versions and operations behind a result |
| PSF | Point spread function describing an imaging system's response to a point source |
| Pseudoreplication | Treating dependent pixels/ROIs/cells as independent biological units |
| QAT / quantization | Training-aware/compressed numerical representation of model weights |
| R² | In-sample fraction of target variation explained by the fitted regression |
| Radius | Center-to-edge distance; not the physical circle editor's diameter |
| Raw | Original acquisition intensities before the applied preparation recipe |
| Registration | Alignment of channels/images; calibration alone does not perform it |
| Residual | Raw minus processed in preparation diagnostics; context differs for regression residuals |
| Resolution | Ability to distinguish structures; not zoom percentage or file dimensions alone |
| Review gate | Explicit confirmation that an image's current settings/ROIs were inspected |
| ROI | Region of interest, here a per-plane circle/polygon or a separately defined line |
| Rolling ball | Curved lower-envelope background estimator with defined spatial/intensity scales |
| Saturation | Values capped by acquisition or display; these have different consequences |
| SD / sigma | Standard deviation; population descriptive SD differs from inferred uncertainty |
| Seed | Recorded initialization for reproducible random/resampling operations |
| Segmentation | Assigning samples to foreground/objects under specified rules |
| Series | One logical image dataset within a file |
| Source coordinate | Index in the native image geometry, before preview scaling |
| Spearman rho | Correlation of average ranks |
| Standardized beta | Regression coefficient after centering/scaling variables |
| Stationarity / translation invariance | Assumption that spatial translations are defensible null comparisons |
| STRING | Reference protein association database; score is not this experiment's binding probability |
| Student-t | Distribution used for the marginal Bayesian mean posterior here |
| Super-resolution | Resolution beyond a stated conventional limit under a validated acquisition/reconstruction method |
| Surface | Rendered boundary geometry, not automatically a measured membrane |
| T / time | Time dimension; time-lapse analysis is not currently included |
| Threshold | Explicit intensity decision level, distinct from LUT/opacity |
| Toroidal shift | Translation with wraparound image boundaries |
| Unavailable | Undefined, absent or rejected value; not numeric zero |
| Unified memory | Memory shared by CPU/GPU/system on the development Mac |
| Validation / biological | Evidence that a measurement/interpretation works for the intended acquisition/biological question |
| Variance | Squared standard deviation, with squared measurement units |
| Version / revision | Software identity / saved-record generation; distinct concepts |
| XYZ spacing | Distances per source sample along each axis |
| Z stretch | Display-only depth exaggeration |

## References and further reading

References explain methods and interpretation; they do not certify this application. Exact implementation conventions in the linked source and exported algorithm version take precedence when reproducing a result. Some older focused documents describe their dated milestone; this manual and current code identify the present user workflow.

### Imaging, processing and quantitative methods

1. [OME-TIFF specification](https://docs.openmicroscopy.org/ome-model/6.2.3/ome-tiff/) — image/metadata representation.
2. [ImageJ: colocalization analysis](https://imagej.net/imaging/colocalization-analysis) — spatial-scale, channel-colour and biological interpretation context.
3. [Fiji Coloc 2](https://imagej.net/plugins/coloc-2) — independent software comparator; OrganelleScope does not claim identical threshold/randomization conventions.
4. [SciPy Pearson correlation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) and [Spearman correlation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html).
5. [SciPy grayscale erosion](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.grey_erosion.html), [opening](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.grey_opening.html) and [Gaussian filtering](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html).
6. [scikit-image rolling-ball background example](https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_rolling_ball.html) — context for spatial versus intensity scaling; no exact ImageJ parity implied.
7. [scikit-image threshold definitions](https://scikit-image.org/docs/stable/api/skimage.filters.html#skimage.filters.threshold_otsu) and [measurement/surface routines](https://scikit-image.org/docs/stable/api/skimage.measure.html).
8. [SciPy Euclidean distance transform](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.distance_transform_edt.html).
9. [SciPy permutation tests](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html).
10. Benjamini & Hochberg (1995), [Controlling the false discovery rate](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x).
11. [NumPy least squares](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html) — numerical regression solver, separate from biological inference.

### Providers, models and viewer design

12. [STRING API](https://string-db.org/help/api/) and [access/licensing](https://string-db.org/cgi/access?footer_active_subpage=licensing).
13. [KEGG REST access](https://www.kegg.jp/kegg/rest/) and [API manual](https://www.kegg.jp/kegg/rest/keggapi.html).
14. [Gemma 4 12B](https://huggingface.co/google/gemma-4-12B-it) and [official QAT weights](https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf).
15. [OpenAI GPT-OSS collection](https://huggingface.co/collections/openai/gpt-oss), [20B documentation](https://developers.openai.com/api/docs/models/gpt-oss-20b), [Harmony](https://developers.openai.com/cookbook/articles/openai-harmony) and [local deployment guidance](https://developers.openai.com/cookbook/articles/gpt-oss/run-transformers).
16. [MicroVQA paper](https://arxiv.org/html/2503.13399v1) — external microscopy reasoning benchmark, not a local Gemma validation.
17. [Llama 3.2 Vision 11B card](https://huggingface.co/meta-llama/Llama-3.2-11B-Vision-Instruct), [Qwen2-VL-7B](https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct), [Pixtral-12B](https://huggingface.co/mistralai/Pixtral-12B-2409) and [LLaVA-Med v1.5](https://huggingface.co/microsoft/llava-med-v1.5-mistral-7b).
18. [napari repository](https://github.com/napari/napari), [Image layers](https://napari.org/stable/howtos/layers/image.html) and [Labels](https://napari.org/stable/howtos/layers/labels.html).
19. [Apple app safety/opening guidance](https://support.apple.com/en-us/102445).

### Primary scientific literature and how it applies

These papers support the concepts identified below. A citation is not an endorsement or validation of OrganelleScope, and a paper's algorithm is not claimed as implemented unless the corresponding chapter says so. Links and bibliographic details were checked on 18 October 2026. Some publisher pages require institutional access; primary full-text links are supplied where available.

20. <a id="ref-dunn2011"></a>Dunn KW, Kamocka MM, McDonald JH (2011). **A practical guide to evaluating colocalization in biological microscopy.** *American Journal of Physiology–Cell Physiology* 300:C723–C742. [DOI: 10.1152/ajpcell.00462.2010](https://doi.org/10.1152/ajpcell.00462.2010); [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC3074624/). Supports distinguishing co-occurrence from proportional intensity correlation, assessing background and selecting a metric for the biological question.
21. <a id="ref-manders1993"></a>Manders EMM, Verbeek FJ, Aten JA (1993). **Measurement of co-localization of objects in dual-colour confocal images.** *Journal of Microscopy* 169:375–382. [DOI: 10.1111/j.1365-2818.1993.tb03313.x](https://doi.org/10.1111/j.1365-2818.1993.tb03313.x); [original paper](https://www.microscopyu.com/pdfs/Manders_etal_JOM_169-375-1993.pdf). Foundational directional colocalization measures; background, cross-talk and noise matter. Consult this manual for the application's exact denominators and threshold boundaries.
22. <a id="ref-costes2004"></a>Costes SV, Daelemans D, Cho EH, Dobbin Z, Pavlakis G, Lockett S (2004). **Automatic and quantitative measurement of protein-protein colocalization in live cells.** *Biophysical Journal* 86:3993–4003. [DOI: 10.1529/biophysj.103.038422](https://doi.org/10.1529/biophysj.103.038422); [primary abstract and full-text links](https://pubmed.ncbi.nlm.nih.gov/15189895/). Methodological source for automatic paired thresholds; OrganelleScope's documented Costes-style implementation is not a claim of identical search, rounding or randomization.
23. <a id="ref-bolte2006"></a>Bolte S, Cordelières FP (2006). **A guided tour into subcellular colocalization analysis in light microscopy.** *Journal of Microscopy* 224:213–232. [DOI: 10.1111/j.1365-2818.2006.01706.x](https://doi.org/10.1111/j.1365-2818.2006.01706.x). Explains common analysis approaches and their interpretation; also informs the factual comparison with JaCoP.
24. <a id="ref-waters2009"></a>Waters JC (2009). **Accuracy and precision in quantitative fluorescence microscopy.** *Journal of Cell Biology* 185:1135–1148. [DOI: 10.1083/jcb.200903097](https://doi.org/10.1083/jcb.200903097); [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC2712964/). Supports acquisition-aware interpretation of intensity, sampling, noise and detector limitations; a display stretch does not correct acquisition errors.
25. <a id="ref-jost2019"></a>Jost APT, Waters JC (2019). **Designing a rigorous microscopy experiment: Validating methods and avoiding bias.** *Journal of Cell Biology* 218:1452–1466. [DOI: 10.1083/jcb.201812109](https://doi.org/10.1083/jcb.201812109); [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC6504886/). Supports independent controls, system-performance checks and reducing selection bias; deterministic software tests alone do not meet those requirements.
26. <a id="ref-montero2021"></a>Montero Llopis P, Senft RA, Ross-Elliott TJ et al. (2021). **Best practices and tools for reporting reproducible fluorescence microscopy methods.** *Nature Methods* 18:1463–1476. [DOI: 10.1038/s41592-021-01156-w](https://doi.org/10.1038/s41592-021-01156-w). Guides recording sample preparation, acquisition hardware/software and analysis settings. Metadata extraction does not establish that every necessary experimental detail was recorded.
27. <a id="ref-lazic2018"></a>Lazic SE, Clarke-Williams CJ, Munafò MR (2018). **What exactly is ‘N’ in cell culture and animal experiments?** *PLOS Biology* 16:e2005282. [DOI and full text: 10.1371/journal.pbio.2005282](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.2005282). Supports identifying experimental units from the intervention and design rather than counting cells, pixels or ROIs indiscriminately.
28. <a id="ref-hurlbert1984"></a>Hurlbert SH (1984). **Pseudoreplication and the design of ecological field experiments.** *Ecological Monographs* 54:187–211. [DOI: 10.2307/1942661](https://doi.org/10.2307/1942661). Foundational treatment of nonindependent observations and inappropriate replication; the principle informs experiment-level inference but does not prescribe a universal microscopy design.
29. <a id="ref-efron1979"></a>Efron B (1979). **Bootstrap methods: Another look at the jackknife.** *Annals of Statistics* 7:1–26. [DOI: 10.1214/aos/1176344552](https://doi.org/10.1214/aos/1176344552). Foundation for resampling-based uncertainty; OrganelleScope's hierarchical bootstrap and small-sample behavior require their own assessment.
30. <a id="ref-otsu1979"></a>Otsu N (1979). **A threshold selection method from gray-level histograms.** *IEEE Transactions on Systems, Man, and Cybernetics* 9:62–66. [DOI: 10.1109/TSMC.1979.4310076](https://doi.org/10.1109/TSMC.1979.4310076). Basis for histogram-based partitioning; an intensity threshold is not a biological classifier or independently validated mask.
31. <a id="ref-lagache2015"></a>Lagache T et al. (2015). **Statistical analysis of molecule colocalization in bioimaging.** *Cytometry Part A*. [DOI: 10.1002/cyto.a.22629](https://doi.org/10.1002/cyto.a.22629). Context for differences between pixel- and object-based methods and sensitivity to image conditions. It does not certify the application's threshold-mask proximity estimator or imply all reviewed methods are implemented.
32. <a id="ref-zinchuk2011"></a>Zinchuk V, Grossenbacher-Zinchuk O (2011). **Quantitative colocalization analysis of confocal fluorescence microscopy images.** *Current Protocols in Cell Biology*, Unit 4.19. [DOI: 10.1002/0471143030.cb0419s52](https://doi.org/10.1002/0471143030.cb0419s52). Practical context for image preparation, coefficient calculation and interpretation; method choices remain explicit in each exported report.

### Citation support and automatic review

33. Gao, T., Yen, H., Yu, J. & Chen, D. (2023). [Enabling Large Language Models to Generate Text with Citations](https://aclanthology.org/2023.emnlp-main.398/). EMNLP, 6465–6488. Citation correctness/completeness are separate from text fluency; this motivates exposing evidence links rather than treating citation presence as correctness. The application's local quotation checks are not the ALCE benchmark or its entailment scorer.
34. Huang, J. et al. (2024). [Large Language Models Cannot Self-Correct Reasoning Yet](https://openreview.net/forum?id=IkmD3fKBPQ). ICLR. The paper studies limitations of intrinsic self-correction in its tested reasoning settings; it does not establish the performance of this Gemma profile. It motivates keeping same-model review explicitly provisional and using external measurements, reference implementations and human review.

### Application-specific methods and evidence

- [Verification status](docs/VALIDATION.md) and [build process](#58-installers-github-actions-and-licensing).
- [Coloc 2 fixtures](docs/validation/COLOC2_BENCHMARK.json), [manual-threshold comparisons](docs/validation/COLOC2_THRESHOLD_BENCHMARK.json), [hierarchical simulation](docs/validation/HIERARCHICAL_SYNTHETIC_BENCHMARK.json) and [Gaussian simulation](docs/validation/INFERENCE_SYNTHETIC_BENCHMARK.json).
- [Cumulative model decisions and preserved assessments](README_MODEL_DECISIONS.md), [assistant setup](#47-what-the-assistant-can-do) and [software comparison](docs/SOFTWARE_COMPARISON.md).
- [Third-party notices](third_party/NOTICE.md) and [release notes](docs/RELEASE_NOTES.md).

For software citation, use the exact version and release URL in [CITATION.cff](CITATION.cff). Cite the original statistical/imaging methods separately; a software citation does not substitute for acquisition or analysis details.
