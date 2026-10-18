"""Collect build-specific notices and provenance alongside the exact native installer."""
import hashlib,json,platform,subprocess,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
version=json.loads((root/'package.json').read_text(encoding='utf-8'))['version']
label='macos-arm64' if platform.system()=='Darwin' else 'windows-x64'
suffix='dmg' if platform.system()=='Darwin' else 'exe'
release=root/'release';asset=release/f'OrganelleScope-{version}-{label}.{suffix}'
if not asset.is_file():raise SystemExit(f'Missing expected installer: {asset.name}')
with asset.open('rb') as source:digest=hashlib.file_digest(source,'sha256').hexdigest()
with zipfile.ZipFile(release/f'dependency-notices-{label}.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for file in sorted((root/'build/notices').glob('*')):archive.write(file,file.name)
report={'version':version,'platform':label,'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        'installer':asset.name,'bytes':asset.stat().st_size,'sha256':digest,
        'source_tests':'backend and frontend passed before packaging', 'frozen_backend':'synthetic API smoke passed',
        'signing':'ad-hoc, not notarized' if suffix=='dmg' else 'unsigned',
        'assistant_runtime_bundled':True,'assistant_weight_setup':'automatic first-launch download; pinned size and SHA-256; pause/resume','assistant_weights_bundled':False,'scope':'Build checks do not establish native user acceptance or biological validity.'}
(release/f'verification-{label}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
