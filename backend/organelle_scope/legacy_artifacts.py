"""Read-only archive compatibility for retired image-restoration results.

No training, inference or processed-plane loading is provided.
"""
import json
from uuid import UUID
from organelle_scope.image_io import ImageError

def result_manifest(root,ident):
    UUID(ident)
    path=root/'restoration-data'/'results'/ident/'manifest.json'
    if not path.is_file():raise ImageError('Historical processing artifact is missing; restore its archive before exporting this project.')
    return json.loads(path.read_text())

def has_retired_processing(value):
    if isinstance(value,list):return any(has_retired_processing(v) for v in value)
    if isinstance(value,dict):return bool(value.get('restoration_result_id')) or any(has_retired_processing(v) for v in value.values())
    return False
