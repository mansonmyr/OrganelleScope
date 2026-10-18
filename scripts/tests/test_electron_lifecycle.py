"""Run the desktop lifecycle regression tests in native installer CI."""
from pathlib import Path
import subprocess,unittest
class LifecycleTests(unittest.TestCase):
    def test_owned_service_readiness_shutdown_and_diagnostics(self):
        root=Path(__file__).resolve().parents[2]
        result=subprocess.run(['node','--test','electron/lifecycle.test.cjs'],cwd=root,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)

    def test_installer_rejects_research_payload(self):
        root=Path(__file__).resolve().parents[2]
        result=subprocess.run(['node','--test','scripts/package-research-audit.test.cjs'],cwd=root,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
