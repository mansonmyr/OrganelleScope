"""Publish both verified platform assets using the ephemeral Actions token only."""
import hashlib,json,os,re,urllib.request
from pathlib import Path

root=Path(__file__).resolve().parents[1]
version=json.loads((root/'package.json').read_text(encoding='utf-8'))['version']
tag=os.environ['GITHUB_REF_NAME']
if not re.fullmatch(r'v'+re.escape(version)+r'(?:-[A-Za-z0-9.]+)?',tag):
    raise SystemExit('Tag must match the application version.')
prerelease='-' in tag
repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GITHUB_TOKEN']
base=f'https://api.github.com/repos/{repo}'
headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}

def request(url,method='GET',payload=None,content_type='application/json'):
    if payload is not None and not isinstance(payload,bytes):payload=json.dumps(payload).encode()
    req=urllib.request.Request(url,data=payload,method=method,headers={**headers,'Content-Type':content_type})
    with urllib.request.urlopen(req,timeout=300) as response:return json.load(response)

folder=root/'release';lines=[];assets=[]
for label,suffix in [('macos-arm64','dmg'),('windows-x64','exe')]:
    asset=folder/f'OrganelleScope-{version}-{label}.{suffix}'
    report=json.loads((folder/f'verification-{label}.json').read_text(encoding='utf-8'))
    if report['version']!=version or report['commit']!=os.environ['GITHUB_SHA']:raise SystemExit('Mixed source revisions in installer artifacts.')
    with asset.open('rb') as source:digest=hashlib.file_digest(source,'sha256').hexdigest()
    if report['sha256']!=digest or report['bytes']!=asset.stat().st_size:raise SystemExit('Installer verification checksum mismatch.')
    if not (folder/f'dependency-notices-{label}.zip').is_file():raise SystemExit('Missing native dependency notices.')
    lines.append(f'{digest}  {asset.name}')
    assets.extend([asset,folder/f'verification-{label}.json',folder/f'dependency-notices-{label}.zip'])
(folder/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
assets.append(folder/'SHA256SUMS.txt')
installer_check=folder/'installer-check-macos-arm64.json'
if installer_check.is_file():assets.append(installer_check)
for name in ('desktop-check-windows-x64.json','workload-macos-arm64.json','workload-windows-x64.json','runtime-check-macos-arm64.json','runtime-check-windows-x64.json'):
 record=folder/name
 if record.is_file():assets.append(record)
if not prerelease:
    for label in ('macos-arm64','windows-x64'):
        workload=json.loads((folder/f'workload-{label}.json').read_text(encoding='utf-8'))
        runtime=json.loads((folder/f'runtime-check-{label}.json').read_text(encoding='utf-8'))
        desktop=json.loads((folder/('installer-check-macos-arm64.json' if label=='macos-arm64' else 'desktop-check-windows-x64.json')).read_text(encoding='utf-8'))
        verified=json.loads((folder/f'verification-{label}.json').read_text(encoding='utf-8'))
        if label=='macos-arm64':
            if desktop.get('sha256')!=verified['sha256']:raise SystemExit('Mac qualification report does not match this installer.')
            if desktop.get('dmg_integrity')!='passed' or desktop.get('app_and_backend_signature_verification')!='passed':raise SystemExit('Mac installer integrity gate failed.')
            desktop=desktop['desktop_temporary_install_startup']
        elif not desktop.get('installer_extracted_and_launched') or desktop.get('installer_sha256')!=verified['sha256']:raise SystemExit('Windows native install gate failed.')
        if desktop.get('version')!=version or desktop.get('successful_launches',0)<3:raise SystemExit('Repeated native startup gate failed.')
        launches=desktop.get('launches',[])
        if len(launches)!=desktop.get('successful_launches') or len(launches)<3 or sum(l.get('profile')=='fresh' for l in launches)<2 or not any(l.get('profile')=='retained' for l in launches):raise SystemExit('Cold/warm startup evidence is incomplete.')
        if not desktop.get('renderer_mounted') or not desktop.get('local_backend_ready') or not desktop.get('diagnostics_available') or not all(l.get('authenticated_backend_ready') and l.get('owned_backend_exit_observed') and l.get('shutdown_complete') for l in desktop.get('launches',[])):raise SystemExit('Startup diagnostics/shutdown gate failed.')
        if runtime.get('native_executable_load')!='passed':raise SystemExit('Bundled inference runtime gate failed.')
        if not all(workload.get(key) for key in ('all_four_cuboid_sums_exact','batch_all_channel_sums_exact','technical_repeated_source_flagged')):raise SystemExit('Native image/batch workload gate failed.')
notes=(root/'docs/RELEASE_NOTES.md').read_text(encoding='utf-8')
for target,relative in [('../MANUAL.md','MANUAL.md'),('VALIDATION.md','docs/VALIDATION.md'),('../CITATION.cff','CITATION.cff')]:
    notes=notes.replace('('+target+')','(https://github.com/'+repo+'/blob/'+tag+'/'+relative+')')
body=notes+'\n\nSee [MANUAL.md](https://github.com/'+repo+'/blob/'+tag+'/MANUAL.md) for installation, features, interpretation and references.\n'
# A failed upload intentionally leaves a draft. Do not silently replace a published asset.
existing=request(base+'/releases?per_page=100')
if any(item['tag_name']==tag for item in existing):raise SystemExit('A release with this tag already exists. Review it before retrying publication.')
release=request(base+'/releases','POST',{'tag_name':tag,'name':f'OrganelleScope {tag}'+(' — release candidate' if prerelease else ''),'body':body,'draft':True,'prerelease':prerelease,'make_latest':'false' if prerelease else 'true'})
url=release['upload_url'].split('{')[0]
for path in assets:
    print(f'Uploading {path.name} ({path.stat().st_size:,} bytes)',flush=True)
    uploaded=request(url+'?name='+path.name,'POST',path.read_bytes(),'application/octet-stream')
    if uploaded['size']!=path.stat().st_size:raise SystemExit('Uploaded asset size mismatch; release remains a draft.')
    expected=hashlib.sha256(path.read_bytes()).hexdigest()
    if uploaded.get('digest') and uploaded['digest']!='sha256:'+expected:raise SystemExit('Uploaded asset digest mismatch; release remains a draft.')
result=request(base+'/releases/'+str(release['id']),'PATCH',{'draft':False})
print('Published '+result['html_url'])
