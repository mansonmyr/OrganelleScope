"""Boot a packaged desktop app with a disposable user profile and model download disabled.
On Windows, first silently install this build into the disposable directory.
"""
import argparse,json,os,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--app',type=Path);p.add_argument('--installer',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
root=Path(__file__).resolve().parents[1];version=json.loads((root/'package.json').read_text(encoding='utf-8'))['version'];output=args.output.resolve()
with tempfile.TemporaryDirectory(prefix='OrganelleScope-desktop-check-') as directory:
 temp=Path(directory);environment={**os.environ,'ORGANELLESCOPE_DISABLE_AUTO_SETUP':'1','ORGANELLESCOPE_SMOKE_DATA':str(temp/'profile'),'ORGANELLESCOPE_SMOKE_REPORT':str(output)}
 if sys.platform=='win32':
  installer=(args.installer or root/'release'/f'OrganelleScope-{version}-windows-x64.exe').resolve();destination=temp/'installed'
  subprocess.run([str(installer),'/S',f'/D={destination}'],env=environment,check=True,timeout=180)
  binary=destination/'OrganelleScope.exe'
 else:
  if args.app is None:p.error('Provide the packaged .app directory on macOS.')
  binary=args.app/'Contents/MacOS/OrganelleScope'
 if output.exists():output.unlink()
 subprocess.run([str(binary),'--organelle-smoke-test'],env=environment,check=True,timeout=150,stdout=subprocess.DEVNULL)
 report=json.loads(output.read_text(encoding='utf-8'))
 assert report['packaged'] and report['renderer_mounted'] and report['local_backend_ready']
 report['installer_extracted_and_launched']=sys.platform=='win32';output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report))
