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
