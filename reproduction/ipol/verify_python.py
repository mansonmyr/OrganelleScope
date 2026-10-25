"""Copyright 2026 Kai Hong Ooi. SPDX-License-Identifier: GPL-3.0-only.
Replay the public P5 example without a GUI, server, Fiji, JDK or TeX.
"""
from pathlib import Path
import argparse, hashlib, importlib.metadata, json, math, platform, sys
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "backend"))
import tifffile
from organelle_scope.cli import calculate, closed_form_demo
from organelle_scope.proximity import proximity_summary

def require(condition, message):
    if not condition:
        raise ValueError(message)

def compare(actual, expected, label):
    if isinstance(expected, dict):
        require(actual.keys() == expected.keys(), label + ": different keys")
        for key in expected:
            compare(actual[key], expected[key], label + "." + key)
    elif isinstance(expected, list):
        require(len(actual) == len(expected), label + ": different lengths")
        for i, value in enumerate(expected):
            compare(actual[i], value, label + f"[{i}]")
    elif isinstance(expected, float):
        require(math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12), label + ": numerical mismatch")
    else:
        require(actual == expected, label + ": mismatch")

def verify(output):
    identity = json.loads((ROOT / "SOURCE-MANIFEST.json").read_text())
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    for name, value in identity["module_sha256"].items():
        require(digest(REPO / "backend/organelle_scope" / name) == value, "Reviewed core changed: " + name)
    for name, value in identity["inputs_and_expected_sha256"].items():
        require(digest(ROOT / name) == value, "Frozen input/result changed: " + name)
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    roi = calculate(ROOT / "data", manifest, "P5", "costes")
    compare(roi, json.loads((ROOT / "expected/P5-roi.json").read_text()), "ROI")
    gui = json.loads((ROOT / "expected/P5-gui-pair.json").read_text())
    require(gui["source_sha256"] == roi["source_sha256"], "GUI source mismatch")
    require(gui["selected_z"] == roi["roi"]["z"] and gui["selected_pixels"] == roi["selected_pixels"], "GUI population mismatch")
    require(gui["roi_points"] == roi["roi"]["points"] and gui["measurement_source"] == "raw", "GUI geometry/settings mismatch")
    compare(gui["pair"], roi["result"], "Recorded GUI pair versus fresh CLI")
    marker = tifffile.imread(ROOT / "data/P5-marker.tif").astype(bool)
    reference = tifffile.imread(ROOT / "data/P5-reference.tif").astype(bool)
    spacing = [manifest[0]["spacing_um"][axis] for axis in "ZYX"]
    reports = [proximity_summary(marker, reference, spacing, cutoff) for cutoff in (.25, .42)]
    compare(reports, json.loads((ROOT / "expected/P5-proximity.json").read_text()), "Proximity")
    output.mkdir(parents=True, exist_ok=True)
    for name, value in [("P5-roi.json", roi), ("P5-proximity.json", reports)]:
        (output / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    summary = {"status": "passed", "reviewed_commit": identity["reviewed_commit"], "closed_form_demo": closed_form_demo()["passed"], "recorded_gui_pair_fields": len(gui["pair"]), "reverse_fraction_at_025": reports[0]["reference_to_marker"]["fraction_within_distance"], "environment": {"platform": platform.platform(), "python": platform.python_version(), "dependencies": {n: importlib.metadata.version(n) for n in ("numpy", "scipy", "pydantic", "tifffile")}}, "scope": "Recalculates one P5 case and compares a previously captured GUI export. Does not launch the GUI, qualify installers, rerun Coloc 2 or reproduce all manuscript tables."}
    (output / "verification.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(verify(parser.parse_args().output), indent=2))
