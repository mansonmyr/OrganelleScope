import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const selectedPython = process.env.ORGANELLESCOPE_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const python = /[\\/]/.test(selectedPython) ? path.resolve(root, selectedPython) : selectedPython;
const result = spawnSync(python, ['-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--name', 'organellescope-backend', '--collect-submodules', 'organelle_scope', '../scripts/backend_entry.py'], { cwd: path.join(root, 'backend'), stdio: 'inherit' });
process.exit(result.status ?? 1);
