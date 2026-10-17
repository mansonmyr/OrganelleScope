import { spawnSync } from 'node:child_process';
import path from 'node:path';
import {mkdirSync} from 'node:fs';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const selectedPython = process.env.ORGANELLESCOPE_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const python = /[\\/]/.test(selectedPython) ? path.resolve(root, selectedPython) : selectedPython;
const managedCache=path.join(root,'backend','build','.runtime-cache');mkdirSync(managedCache,{recursive:true});
const buildEnvironment={...process.env,MPLCONFIGDIR:path.join(managedCache,'matplotlib'),XDG_CACHE_HOME:managedCache};
const flags=['--exclude-module','careamics','--exclude-module','torch','--exclude-module','torchvision','--exclude-module','lightning','--exclude-module','pytorch_lightning'];
const result = spawnSync(python, ['-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--name', 'organellescope-backend', '--paths', '.', '--collect-submodules', 'organelle_scope',...flags, '../scripts/backend_entry.py'], {
  cwd: path.join(root, 'backend'), stdio: 'inherit',
  env: { ...buildEnvironment, PYINSTALLER_CONFIG_DIR: path.join(root, 'backend', 'build', '.pyinstaller-cache') }
});
process.exit(result.status ?? 1);
