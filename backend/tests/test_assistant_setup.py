import hashlib
import importlib.util
import json
from pathlib import Path
import pytest


def setup_module_for_test(tmp_path,monkeypatch):
 script=Path(__file__).resolve().parents[2]/'scripts/setup-local-assistant.py'
 spec=importlib.util.spec_from_file_location('assistant_setup_test',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 monkeypatch.setattr(module,'ROOT',tmp_path);monkeypatch.setattr(module.platform,'system',lambda:'Darwin');monkeypatch.setattr(module.platform,'machine',lambda:'arm64')
 monkeypatch.setattr(module.sys,'argv',['setup-local-assistant.py','--download'])
 root=tmp_path/'.local-runtime';binary=root/'llama-b11669/llama-server';binary.parent.mkdir(parents=True);binary.write_bytes(b'verified binary')
 digest=hashlib.sha256(binary.read_bytes()).hexdigest()
 (root/'installed-runtime.json').write_text(json.dumps({'archive_sha256':module.RUNTIMES['Darwin-arm64']['sha256'],'files':{'llama-server':digest}}))
 return module,binary


def test_verified_runtime_receipt_avoids_archive_redownload(tmp_path,monkeypatch):
 module,binary=setup_module_for_test(tmp_path,monkeypatch);calls=[]
 monkeypatch.setattr(module,'download',lambda url,*args:calls.append(url))
 module.main()
 assert len(calls)==1 and calls[0].startswith(module.MODEL['quantization']+'/resolve/')


def test_modified_runtime_is_not_accepted_from_receipt(tmp_path,monkeypatch):
 module,binary=setup_module_for_test(tmp_path,monkeypatch);binary.write_bytes(b'changed');calls=[]
 def download(url,*args):
  calls.append(url)
  if 'github.com' in url:raise ValueError('fresh verified archive required')
 monkeypatch.setattr(module,'download',download)
 with pytest.raises(ValueError,match='fresh verified archive'):module.main()
 assert len(calls)==2
