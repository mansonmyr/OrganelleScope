"""Repeat native cold/warm startup with isolated profiles; retain diagnostics on failure."""
import argparse,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--app',type=Path);p.add_argument('--installer',type=Path);p.add_argument('--launches',type=int,default=3);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
if not 3<=args.launches<=10:p.error('Use three to ten launches to cover cold and warm profiles.')
root=Path(__file__).resolve().parents[1];version=json.loads((root/'package.json').read_text(encoding='utf-8'))['version'];output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='OrganelleScope-desktop-check-') as directory:
 temp=Path(directory);base_env={**os.environ,'ORGANELLESCOPE_DISABLE_AUTO_SETUP':'1'}
 if sys.platform=='win32':
  installer=(args.installer or root/'release'/f'OrganelleScope-{version}-windows-x64.exe').resolve();destination=temp/'installed'
  subprocess.run([str(installer),'/S',f'/D={destination}'],env=base_env,check=True,timeout=180)
  binary=destination/'OrganelleScope.exe'
 else:
  if args.app is None:p.error('Provide the packaged .app directory on macOS.')
  binary=args.app/'Contents/MacOS/OrganelleScope'
 launches=[]
 for index in range(args.launches):
  profile=temp/(f'profile-{index//3}' if index%3<2 else f'profile-{index}-fresh')
  report_path=temp/f'launch-{index}.json'
  environment={**base_env,'ORGANELLESCOPE_SMOKE_DATA':str(profile),'ORGANELLESCOPE_SMOKE_REPORT':str(report_path)}
  try:
   result=subprocess.run([str(binary),'--organelle-smoke-test'],env=environment,timeout=150,capture_output=True,text=True)
   log=profile/'logs/startup.jsonl'
   events=[json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()] if log.is_file() else []
   if result.returncode!=0:raise RuntimeError(f'Native launch exited {result.returncode}: {result.stderr[-6000:]}')
   report=json.loads(report_path.read_text(encoding='utf-8'))
   assert report['packaged'] and report['renderer_mounted'] and report['local_backend_ready'] and report['diagnostics_available']
   # On a warm launch, only inspect the most recent session in the append-only log.
   start=max(i for i,e in enumerate(events) if e['event']=='launch');events=events[start:]
   names=[event['event'] for event in events]
   assert all(name in names for name in ['backend-ready','window-loaded','backend-exit','shutdown-complete']),names
   assert not any(e['event']=='startup-failed' or e['event']=='renderer-stopped' and e.get('reason')!='clean-exit' for e in events),events
   launches.append({'index':index+1,'profile':'retained' if index%3==1 else 'fresh','renderer_mounted':True,'authenticated_backend_ready':True,'owned_backend_exit_observed':True,'shutdown_complete':True})
  except Exception as exc:
   failure={'version':version,'launch_index':index+1,'error':str(exc),'stderr':locals().get('result').stderr[-6000:] if locals().get('result') else None,'events':locals().get('events',[])}
   output.with_suffix('.failure.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8')
   raise RuntimeError(json.dumps(failure)) from exc
 report['installer_extracted_and_launched']=sys.platform=='win32'
 if sys.platform=='win32':
  with installer.open('rb') as stream:report['installer_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
 report['successful_launches']=len(launches);report['launches']=launches
 report['scope']=f'Repeated native startup: {sum(l["profile"]=="fresh" for l in launches)} fresh and {sum(l["profile"]=="retained" for l in launches)} retained-profile launches, authenticated service readiness, renderer paint and observed owned-backend shutdown. Model download disabled; not full human usability or biological validation.'
 output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
