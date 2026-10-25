"""Copyright 2026 Kai Hong Ooi. SPDX-License-Identifier: GPL-3.0-only."""
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2] / "reproduction/ipol"

def runner():
    spec = importlib.util.spec_from_file_location("manuscript_replay", ROOT / "verify_python.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_manuscript_p5_replay(tmp_path):
    report = runner().verify(tmp_path / "replay")
    assert report["recorded_gui_pair_fields"] == 13
    assert report["reverse_fraction_at_025"] == pytest.approx(826 / 839, abs=1e-15)

def test_replay_rejects_constant_one_proximity():
    expected = json.loads((ROOT / "expected/P5-proximity.json").read_text())[0]
    broken = json.loads(json.dumps(expected))
    broken["reference_to_marker"]["fraction_within_distance"] = 1.0
    with pytest.raises(ValueError, match="numerical mismatch"):
        runner().compare(broken, expected, "Proximity")

def test_replay_rejects_changed_recorded_gui_value():
    original = json.loads((ROOT / "expected/P5-roi.json").read_text())["result"]
    changed = dict(original, pcc=0.0)
    with pytest.raises(ValueError, match="numerical mismatch"):
        runner().compare(changed, original, "Recorded GUI pair versus fresh CLI")


def test_hashed_replay_files_preserve_bytes_with_windows_checkout():
    import subprocess
    repository = ROOT.parents[1]
    manifest = json.loads((ROOT / "SOURCE-MANIFEST.json").read_text())
    paths = ["backend/organelle_scope/" + name for name in manifest["module_sha256"]]
    paths += ["reproduction/ipol/" + name for name in manifest["inputs_and_expected_sha256"]]
    for relative in paths:
        current = (repository / relative).read_bytes()
        checkout = subprocess.run(
            ["git", "-c", "core.autocrlf=true", "hash-object", "--path=" + relative, "--stdin"],
            input=current, cwd=repository, check=True, capture_output=True,
        ).stdout.strip()
        # --no-filters hashes literal bytes; equality proves checkout filters
        # cannot silently normalize a different byte sequence before hashing.
        raw = subprocess.run(
            ["git", "hash-object", "--no-filters", "--stdin"],
            input=current, cwd=repository, check=True, capture_output=True,
        ).stdout.strip()
        assert checkout == raw, relative
        if not relative.endswith(".tif"):
            attributes = subprocess.run(
                ["git", "check-attr", "eol", "--", relative], cwd=repository,
                check=True, capture_output=True, text=True,
            ).stdout.strip()
            assert attributes.endswith(": lf"), relative
