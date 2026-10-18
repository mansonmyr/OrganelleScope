"""Existing Linux CI exercises a genuinely enforced process budget."""
import json,os,subprocess,sys
from pathlib import Path
import pytest


@pytest.mark.skipif(sys.platform!='linux',reason='Linux RLIMIT_AS worker; no claim of equivalent macOS/Windows enforcement.')
def test_source_volume_and_roi_under_hard_memory_budget():
    root=Path(__file__).resolve().parents[2]
    result=subprocess.run([sys.executable,str(root/'scripts/validation/limited_memory_worker.py'),'--address-limit-mib','1536'],cwd=root,env={**os.environ,'PYTHONPATH':str(root/'backend'),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'},capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    report=json.loads(result.stdout.strip().splitlines()[-1]);assert report['status']=='passed' and report['volume_and_roi_exact']
    assert report['hard_address_space_limit_bytes']==1536*1024**2
    print(json.dumps(report))
