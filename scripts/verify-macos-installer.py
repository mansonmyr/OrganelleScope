"""Read-only DMG/signature/frontend check and synthetic packaged-service smoke test.
Run on macOS after packaging. The installed application is not touched.
"""
import argparse,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dmg',type=Path)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
version=json.loads((root/'package.json').read_text(encoding='utf-8'))['version']
dmg=(args.dmg or root/'release'/f'OrganelleScope-{version}-macos-arm64.dmg').resolve()
if sys.platform!='darwin' or not dmg.is_file():parser.error('Select an existing macOS disk image on a Mac.')

def run(arguments,**kwargs):
    return subprocess.run(arguments,check=True,capture_output=True,text=True,**kwargs)

run(['/usr/bin/hdiutil','verify',str(dmg)])
with tempfile.TemporaryDirectory(prefix='OrganelleScope-installer-check-') as temporary:
    mount=Path(temporary)/'mount';mount.mkdir();attached=False
    try:
        run(['/usr/bin/hdiutil','attach','-readonly','-nobrowse','-mountpoint',str(mount),str(dmg)]);attached=True
        app=mount/'OrganelleScope.app'
        binary=app/'Contents/Resources/backend/organellescope-backend'
        run(['/usr/bin/codesign','--verify','--deep','--strict',str(app)])
        run(['/usr/bin/codesign','--verify','--deep','--strict',str(binary)])
        source_check="""const asar=require('@electron/asar'),fs=require('node:fs'),crypto=require('node:crypto');
const archive=process.argv[1],root=process.argv[2];
const source=fs.readFileSync(root+'/frontend/dist/index.html'),packed=asar.extractFile(archive,'frontend/dist/index.html');
if(!source.equals(packed))throw Error('Packaged frontend differs from verified source build');
const info=JSON.parse(asar.extractFile(archive,'package.json').toString());
console.log(JSON.stringify({version:info.version,frontend_index_sha256:crypto.createHash('sha256').update(packed).digest('hex')}));"""
        front=json.loads(run(['node','-e',source_check,str(app/'Contents/Resources/app.asar'),str(root)],cwd=root).stdout)
        environment={**os.environ,'ORGANELLESCOPE_FROZEN_BACKEND':str(binary)}
        result=run([sys.executable,str(root/'scripts/smoke-frozen.py')],env=environment,cwd=root)
        smoke=json.loads(result.stdout.strip().splitlines()[-1])
        report={'artifact':dmg.name,'bytes':dmg.stat().st_size,'sha256':hashlib.file_digest(dmg.open('rb'),'sha256').hexdigest(),
                'dmg_integrity':'passed','app_and_backend_signature_verification':'passed','signing':'ad-hoc development; not Apple Developer ID/notarized',
                'frontend':front,'mounted_packaged_backend':smoke,'assistant_weights_bundled':False,
                'scope':'Read-only DMG mounting, signature/frontend checks and synthetic backend API checks. No installed-app overwrite, native Windows test, full Electron interaction qualification or biological validation.'}
        args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    finally:
        if attached:run(['/usr/bin/hdiutil','detach',str(mount)])
