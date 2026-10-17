"""Collect installed Python dependency license texts; records a build-environment superset."""
import importlib.metadata as md,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=[];inventory=[]
for dist in sorted(md.distributions(),key=lambda d:d.metadata['Name'].lower()):
    name=dist.metadata['Name'];inventory.append({'name':name,'version':dist.version})
    for item in dist.files or []:
        path=Path(item)
        if '.dist-info' not in str(path) or not any(t in path.name.lower() for t in ['license','copying','notice']):continue
        file=dist.locate_file(item)
        if not file.is_file() or file.stat().st_size>4*1024**2:continue
        try:text=file.read_text()
        except (UnicodeError,OSError):continue
        out.append(f'\n===== {name} {dist.version}: {path.name} =====\n'+'\n'.join(line.rstrip() for line in text.splitlines())+'\n')
(root/'third_party/PYTHON_DEPENDENCY_NOTICES.txt').write_text('License texts found in the build environment, including test/build dependencies. This is a superset, not a claim all packages are shipped. Regenerate for each native build.\n'+''.join(out))
(root/'docs/BUILD_ENVIRONMENT.json').write_text(json.dumps({'scope':'Local build/test environment; superset of installer dependencies','packages':inventory},indent=2)+'\n')
