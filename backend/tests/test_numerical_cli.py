"""Copyright 2026 Kai Hong Ooi. SPDX-License-Identifier: GPL-3.0-only."""
import json
import numpy as np
import pytest
import tifffile
from organelle_scope.cli import closed_form_demo,calculate,main

def test_closed_form_reference_table():
    report=closed_form_demo()
    assert report['passed']
    assert report['actual']['anisotropic_distance_um']==pytest.approx(np.sqrt(5))
    assert report['actual']['manual_m1']==pytest.approx(5/6)

def test_cli_requires_exact_shared_pixels(tmp_path):
    image=tmp_path/'image.tif';tifffile.imwrite(image,np.arange(25,dtype=np.uint16).reshape(5,5))
    manifest=[{'id':'sample','filename':image.name,'sha256':'0'*64}]
    with pytest.raises(ValueError,match='digest'):
        calculate(tmp_path,manifest,'sample','zero')

def test_demo_writes_finite_json_without_desktop(tmp_path,monkeypatch):
    target=tmp_path/'result.json'
    monkeypatch.setattr('sys.argv',['organellescope-core','demo','--output',str(target)])
    main()
    assert json.loads(target.read_text())['passed'] is True
