# Manuscript P5 numerical replay

This focused example supports the current manuscript's P5 ROI, proximity and
recorded interface-to-CLI comparison. It does **not** replace the full reviewer
archive: its simulations, Fiji steppers and manuscript rendering remain in that
separately delivered archive. No publicly hosted online demo is provided.

From the repository root, using Python 3.11 or newer:

```sh
python -m venv .venv-replay
# Activate .venv-replay using your platform's normal activation command.
python -m pip install -r reproduction/ipol/requirements.txt
python reproduction/ipol/verify_python.py --output replay/P5
```

Only four numerical dependencies are installed; the backend is imported directly
from this repository. There is no backend package build, Node, Electron, model,
Fiji, JDK or TeX requirement. Dependency installation needs network access unless
a compatible wheelhouse is supplied (`--no-index --find-links /path/to/wheels`).
After installation, verification uses local files and makes no network requests.
Do not install `./backend` for this focused route.

The output `verification.json` records the actual OS, Python and dependency
versions. Frozen input/output and six module hashes are checked before replay;
a changed reviewed module causes a clear refusal rather than silently comparing
a different implementation. Numerical values use absolute tolerance 1e-12.
The `SOURCE-MANIFEST.json` identifies the reviewed numerical commit separately
from later documentation/test additions.

## Direct CLI commands

These commands also run from the repository root after dependency setup:

```sh
PYTHONPATH=backend python -m organelle_scope.cli roi --data reproduction/ipol/data --sample P5 --mode costes --output replay/P5-roi.json
PYTHONPATH=backend python -m organelle_scope.cli proximity --marker reproduction/ipol/data/P5-marker.tif --reference reproduction/ipol/data/P5-reference.tif --spacing 0.39999999999999997 0.06500000162500004 0.06500000162500004 --cutoff 0.25 --output replay/P5-proximity-025.json
```

For Windows PowerShell, first set `$env:PYTHONPATH="backend"`, then omit the
`PYTHONPATH=backend` prefix. Use cutoff `0.42` for the second manuscript comparison.
The cross-platform verification command above requires no environment variable.

Expected ROI: 185 pixels, zero-based Z=1, Pearson `pcc` = 0.8565728705818413,
thresholded M1 = 0.9415648327219188 and M2 = 0.943940142185923.
At cutoff 0.25 µm, foreground counts are 576/839 and within-distance counts
576/826. `marker_to_reference.fraction_within_distance` = 1.0;
`reference_to_marker.fraction_within_distance` = 0.9845053635280095.
The reverse `p95_occupied_voxel_center_um` = 0.19500000487500013 µm.
Nearest and median distances are zero in both directions. At 0.42 µm both
fractions are 1.0. These containment-sensitive values do not establish binding.

## Provenance and scope

P5 is a retrospectively selected illustrative gamma-tubulin/pericentrin window.
Its pixels and masks are licensed CC BY 4.0; see `data/LICENSE.txt`. Mask inputs
are the frozen threshold-derived masks used by the manuscript, not fresh segmentations.
The publication permission does not apply to other local research files.
`expected/P5-gui-pair.json` is a projection of the genuine 2026-10-25 browser
export onto the selected pair and matching geometry, excluding unrelated workspace
fields. `GUI-CLI-COMPARISON.json` retains the original comparison and full export
hash. The recorded 13-field exact match was one calculation/export through the
frozen frontend/backend. Replaying it checks the saved record against fresh core
results; it does not repeat a live GUI or native installation test.

The acquired P5 **manifest Z step** is 0.39999999999999997 µm. The synthetic
float32-conversion boundary-fixture spacing 0.4000000059604645 µm is a separate
precision example, not P5 acquisition provenance. Four P5 planes span 1.20 µm
between centres; the 1.60 µm interface extent uses four voxel widths and is not
a distance cutoff. No new tolerance or numerical threshold rule is introduced.

These source-only fixtures are outside installer resource lists. They must never
be loaded as a new user's workspace or bundled into the installed application.
