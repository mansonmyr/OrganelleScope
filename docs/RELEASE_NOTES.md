# OrganelleScope 0.2.7 research preview

Batch images now include channel-identity editing and selected-plane signal checks beside their ROIs. Corrected names preserve geometry and require review again. Backend metadata checks prevent a stale batch review being used after channel/metadata changes; historical frozen runs retain their original annotations.

Experimental design review shows labelled experiments/cells, missing labels and repeated source hashes. The frozen run and Excel export retain the design review. Identical raw sources assigned to different conditions or experiments are rejected by experiment inference. Counts do not prove experimental independence.

The assistant receives explicit method guidance on marker identity, corrected annotations, copied TIFFs and nonlinear clipping. Unqualified biological-ground-truth claims about corrected channel labels are withheld, and duplicate advice prefixes are normalized. Synthetic evaluation records preserve the initial inconsistent fixture, corrected follow-up and remaining same-model audit limitations. This is not a biomedical accuracy certification.

Local sample-control reports record owner acceptance/rejection per candidate and preserve rejected technical results. No private image, annotation or measurement is uploaded. Existing background subtraction and Gaussian smoothing remain; denoising and deconvolution remain removed.

The installed application bundles its pinned inference runtime and automatically downloads Gemma once (6.98 GB), with pause/resume and checksum verification. Native build checks, platform reports and checksums accompany each release candidate. Trusted publisher signing remains outside scope.

See the [manual](../MANUAL.md), [verification status](VALIDATION.md) and [model assessments](../README_MODEL_DECISIONS.md).
