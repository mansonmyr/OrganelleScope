"""Write streaming SHA-256 hashes of the exact installers selected for release."""
import hashlib
from pathlib import Path
root=Path('release');lines=[]
for path in sorted(root.glob('*')):
    if path.suffix.lower() not in ('.dmg','.exe','.zip'):continue
    h=hashlib.sha256()
    with path.open('rb') as source:
        while chunk:=source.read(4*1024**2):h.update(chunk)
    lines.append(h.hexdigest()+'  '+path.name)
if not lines:raise SystemExit('No installer assets were built.')
(root/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n')
