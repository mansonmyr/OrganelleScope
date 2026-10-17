"""Conservative cleanup of explicitly managed, superseded assistant assets only."""
from pathlib import Path

RETIRED_MODELS=('Qwen3.5-4B-Q4_K_M.gguf','Ministral-3-8B-Instruct-2512-Q4_K_M.gguf')
# Development-only scratch files from the previous model evaluation. Projects are elsewhere.
RETIRED_SCRATCH=('smoke-project-id.txt','debug-calls.json','evidence-smoke-result.json','final-local-smoke.json','smoke-results.json')
RUNTIME_ARCHIVES=('llama-b11669-bin-macos-arm64.tar.gz','llama-b11669-bin-win-cpu-x64.zip')


def cleanup_superseded(repository:Path,active_model:Path):
    root=repository.resolve();models=root/'.local-models'
    if models.is_symlink() or active_model.is_symlink() or active_model.resolve().parent!=models.resolve() or not active_model.is_file():
        return {'removed':[],'freed_bytes':0,'skipped':'The active model is outside the managed model folder.'}
    candidates=[models/name for name in (*RETIRED_MODELS,*RETIRED_SCRATCH)]
    candidates += [models/(name+'.part') for name in RETIRED_MODELS]
    candidates += [root/'.local-runtime'/name for name in RUNTIME_ARCHIVES]
    # Never follow a symlink, walk arbitrary folders or touch scientific data/evidence caches.
    removed=[];freed=0
    for path in candidates:
        if path.parent.is_symlink() or path.is_symlink() or path.resolve()==active_model.resolve() or not path.is_file():continue
        try:
            size=path.stat().st_size;path.unlink();freed+=size;removed.append(str(path.relative_to(root)))
        except OSError:continue # A failed cleanup must not discard a successful analysis response.
    scratch=models/'debug-logs'/'local-assistant.log'
    if scratch.is_file() and not scratch.is_symlink() and scratch.parent.resolve()==(models/'debug-logs').absolute():
        try:
            size=scratch.stat().st_size;scratch.unlink();freed+=size;removed.append(str(scratch.relative_to(root)))
            if not any(scratch.parent.iterdir()):scratch.parent.rmdir()
        except OSError:pass
    return {'removed':removed,'freed_bytes':freed}
