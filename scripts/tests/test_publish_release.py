"""Exercise release preflight and publication ordering without network access."""
import hashlib,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

SOURCE=(Path(__file__).resolve().parents[1]/'publish-release.py').read_text()

class Response:
    def __init__(self,value):self.value=value
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps(self.value).encode()

class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name);self.calls=[]
        (self.root/'docs').mkdir();(self.root/'release').mkdir()
        (self.root/'package.json').write_text('{"version":"0.2.5"}')
        (self.root/'docs/RELEASE_NOTES.md').write_text('Research preview')
        for label,suffix in [('macos-arm64','dmg'),('windows-x64','exe')]:
            name=f'OrganelleScope-0.2.5-{label}.{suffix}';data=label.encode()
            (self.root/'release'/name).write_bytes(data)
            (self.root/'release'/f'dependency-notices-{label}.zip').write_bytes(b'test-notices')
            (self.root/'release'/f'verification-{label}.json').write_text(json.dumps({'version':'0.2.5','commit':'test-commit','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}))
        (self.root/'release/old-private-report.json').write_text('Do not upload unrelated local files')

    def run_publish(self,tag='v0.2.5-rc.1',fail_upload=False):
        def urlopen(req,timeout):
            self.calls.append(req)
            if req.method=='GET':return Response([])
            if '?name=' in req.full_url:
                if fail_upload:raise OSError('Simulated interrupted upload')
                return Response({'size':len(req.data),'digest':'sha256:'+hashlib.sha256(req.data).hexdigest()})
            return Response({'id':42,'upload_url':'https://uploads.example/assets{?name,label}','html_url':'https://example/release'})
        with patch.dict(os.environ,{'GITHUB_REF_NAME':tag,'GITHUB_REPOSITORY':'test/repo','GITHUB_TOKEN':'fake-token','GITHUB_SHA':'test-commit'}),patch('urllib.request.urlopen',urlopen),patch('builtins.print'):
            exec(compile(SOURCE,'publish-release.py','exec'),{'__file__':str(self.root/'scripts/publish-release.py'),'__name__':'__main__'})

    def test_both_verified_assets_publish_after_uploads(self):
        self.run_publish()
        self.assertEqual(self.calls[-1].method,'PATCH')
        self.assertFalse(json.loads(self.calls[-1].data)['draft'])
        uploads=[r.full_url for r in self.calls if '?name=' in r.full_url]
        self.assertEqual(len(uploads),7)
        self.assertTrue(any('windows-x64.exe' in u for u in uploads))
        self.assertTrue(any('macos-arm64.dmg' in u for u in uploads))
        self.assertFalse(any('old-private-report' in u for u in uploads))
        creation=json.loads(next(r.data for r in self.calls if r.method=='POST' and '?name=' not in r.full_url))
        self.assertTrue(creation['draft']);self.assertTrue(creation['prerelease'])

    def test_tampered_installer_never_contacts_github(self):
        (self.root/'release/OrganelleScope-0.2.5-windows-x64.exe').write_bytes(b'tampered')
        with self.assertRaises(SystemExit):self.run_publish()
        self.assertFalse(self.calls)

    def test_mixed_commits_never_contact_github(self):
        p=self.root/'release/verification-windows-x64.json';record=json.loads(p.read_text());record['commit']='other';p.write_text(json.dumps(record))
        with self.assertRaises(SystemExit):self.run_publish()
        self.assertFalse(self.calls)

    def test_wrong_tag_never_contacts_github(self):
        with self.assertRaises(SystemExit):self.run_publish('v0.2.6-rc.1')
        self.assertFalse(self.calls)

    def test_upload_failure_leaves_draft(self):
        with self.assertRaises(OSError):self.run_publish(fail_upload=True)
        self.assertFalse(any(r.method=='PATCH' for r in self.calls))


class StableReleaseTests(unittest.TestCase):
    setUp=ReleaseTests.setUp
    run_publish=ReleaseTests.run_publish
    def stable_reports(self):
        for label in ('macos-arm64','windows-x64'):
            desktop={'version':'0.2.5','successful_launches':3,'diagnostics_available':True,'renderer_mounted':True,'local_backend_ready':True,'installer_extracted_and_launched':True,'installer_sha256':hashlib.sha256(label.encode()).hexdigest(),'launches':[{'profile':profile,'authenticated_backend_ready':True,'owned_backend_exit_observed':True,'shutdown_complete':True} for profile in ['fresh','retained','fresh']]}
            if label=='macos-arm64':desktop={'sha256':hashlib.sha256(label.encode()).hexdigest(),'dmg_integrity':'passed','app_and_backend_signature_verification':'passed','desktop_temporary_install_startup':desktop}
            name='installer-check-macos-arm64.json' if label=='macos-arm64' else 'desktop-check-windows-x64.json'
            (self.root/'release'/name).write_text(json.dumps(desktop))
            (self.root/'release'/f'runtime-check-{label}.json').write_text(json.dumps({'native_executable_load':'passed'}))
            (self.root/'release'/f'workload-{label}.json').write_text(json.dumps({'all_four_cuboid_sums_exact':True,'batch_all_channel_sums_exact':True,'technical_repeated_source_flagged':True}))

    def test_stable_release_requires_complete_qualification_before_network(self):
        with self.assertRaises(FileNotFoundError):self.run_publish('v0.2.5')
        self.assertFalse(self.calls)
        self.stable_reports();self.run_publish('v0.2.5')
        creation=json.loads(next(r.data for r in self.calls if r.method=='POST' and '?name=' not in r.full_url))
        self.assertFalse(creation['prerelease']);self.assertEqual(creation['make_latest'],'true')

    def test_warm_launch_failure_or_missing_workload_blocks_stable_publication(self):
        self.stable_reports()
        p=self.root/'release/desktop-check-windows-x64.json';d=json.loads(p.read_text());d['successful_launches']=2;p.write_text(json.dumps(d))
        with self.assertRaises(SystemExit):self.run_publish('v0.2.5')
        self.assertFalse(self.calls)

if __name__=='__main__':unittest.main()
