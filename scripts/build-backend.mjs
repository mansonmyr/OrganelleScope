import { spawnSync } from 'node:child_process';
import path from 'node:path';
import {mkdirSync} from 'node:fs';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const selectedPython = process.env.ORGANELLESCOPE_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const python = /[\\/]/.test(selectedPython) ? path.resolve(root, selectedPython) : selectedPython;
const restoration=process.env.ORGANELLESCOPE_INCLUDE_RESTORATION==='1';
const managedCache=path.join(root,'backend','build','.runtime-cache');mkdirSync(managedCache,{recursive:true});
const buildEnvironment={...process.env,MPLCONFIGDIR:path.join(managedCache,'matplotlib'),XDG_CACHE_HOME:managedCache};
const flags=restoration?['--recursive-copy-metadata','careamics','--collect-data','bioimageio.spec','--copy-metadata','bioimageio.spec','--collect-all','careamics','--collect-all','lightning','--collect-all','pytorch_lightning']:['--exclude-module','careamics','--exclude-module','torch','--exclude-module','torchvision','--exclude-module','lightning','--exclude-module','pytorch_lightning'];
if(restoration){const check=spawnSync(python,['-c','import careamics,torch,torchvision; assert careamics.__version__ == "0.3.4"'],{stdio:'inherit',env:buildEnvironment});if(check.status!==0)throw new Error('Install backend[restoration] before building the full restoration edition.');}
const result = spawnSync(python, ['-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--name', 'organellescope-backend', '--paths', '.', '--collect-submodules', 'organelle_scope',...flags, '../scripts/backend_entry.py'], {
  cwd: path.join(root, 'backend'), stdio: 'inherit',
  env: { ...buildEnvironment, PYINSTALLER_CONFIG_DIR: path.join(root, 'backend', 'build', '.pyinstaller-cache') }
});
process.exit(result.status ?? 1);
