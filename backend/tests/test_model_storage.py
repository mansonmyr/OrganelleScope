from pathlib import Path
from organelle_scope.model_storage import cleanup_superseded


def test_cleanup_removes_only_known_superseded_assets(tmp_path):
 models=tmp_path/'.local-models';models.mkdir();runtime=tmp_path/'.local-runtime';runtime.mkdir()
 active=models/'Ministral.gguf';active.write_bytes(b'current')
 (models/'Qwen3.5-4B-Q4_K_M.gguf').write_bytes(b'retired')
 (models/'debug-calls.json').write_bytes(b'old')
 (runtime/'llama-b11669-bin-macos-arm64.tar.gz').write_bytes(b'archive')
 other=models/'my-custom-model.gguf';other.write_bytes(b'keep')
 project=tmp_path/'project-data';project.mkdir();(project/'experiment.json').write_text('keep')
 report=cleanup_superseded(tmp_path,active)
 assert report['freed_bytes']==7+3+7 and len(report['removed'])==3
 assert active.read_bytes()==b'current' and other.exists() and (project/'experiment.json').exists()
 assert cleanup_superseded(tmp_path,active)['freed_bytes']==0


def test_cleanup_does_not_follow_links_or_remove_active_weights(tmp_path):
 models=tmp_path/'.local-models';models.mkdir();outside=tmp_path/'user-model';outside.write_bytes(b'user data')
 active=models/'Qwen3.5-4B-Q4_K_M.gguf';active.write_bytes(b'active')
 (models/'debug-calls.json').symlink_to(outside)
 assert cleanup_superseded(tmp_path,active)['freed_bytes']==0
 assert active.exists() and outside.exists()
 assert cleanup_superseded(tmp_path,outside)['removed']==[]


def test_cleanup_rejects_symlinked_managed_directory(tmp_path):
 outside=tmp_path/'elsewhere';outside.mkdir();(outside/'active.gguf').write_bytes(b'active');(outside/'Qwen3.5-4B-Q4_K_M.gguf').write_bytes(b'keep')
 (tmp_path/'.local-models').symlink_to(outside,target_is_directory=True)
 assert cleanup_superseded(tmp_path,tmp_path/'.local-models/active.gguf')['freed_bytes']==0
 assert (outside/'Qwen3.5-4B-Q4_K_M.gguf').exists()
