"""A Windows legacy code page must not corrupt UTF-8 dependency metadata."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('notices',Path(__file__).resolve().parents[1]/'dependency-notices.py')
notices=importlib.util.module_from_spec(spec);spec.loader.exec_module(notices)

class NoticeTests(unittest.TestCase):
    def test_utf8_manifest_with_non_utf8_system_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);folder=root/'frontend/node_modules/example';folder.mkdir(parents=True)
            (root/'frontend/package-lock.json').write_text(json.dumps({'packages':{'node_modules/example':{'version':'1.0.0'}}}),encoding='utf-8')
            (folder/'package.json').write_text(json.dumps({'name':'example','version':'1.0.0','description':'显微镜 ā','license':'MIT'},ensure_ascii=False),encoding='utf-8')
            (folder/'LICENSE').write_text('Copyright — retained licence notice',encoding='utf-8')
            original=Path.read_text
            def read_as_windows(path,encoding=None,errors=None):
                return original(path,encoding=encoding or 'cp1252',errors=errors)
            with patch.object(notices,'ROOT',root),patch.object(Path,'read_text',read_as_windows):
                inventory,texts=notices.collect_javascript()
            self.assertEqual(inventory[0]['name'],'example')
            self.assertIn('Copyright — retained licence notice',texts[0])

if __name__=='__main__':unittest.main()
