import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const selectedPython = process.env.ORGANELLESCOPE_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const python = /[\\/]/.test(selectedPython) ? path.resolve(root, selectedPython) : selectedPython;
const service = spawn(python, ['-m', 'organelle_scope.main', '--data-dir', path.join(root, '.dev-images')], {
  cwd: path.join(root, 'backend'), stdio: 'inherit', env: { ...process.env, ORGANELLESCOPE_SESSION_TOKEN: 'development-only' }
});
const vite = spawn(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'dev'], { cwd: path.join(root, 'frontend'), stdio: 'inherit' });
let stopping = false;
function stop(code = 0) { if (stopping) return; stopping = true; service.kill(); vite.kill(); process.exit(code); }
service.on('error', e => { console.error(e); stop(1); }); vite.on('error', e => { console.error(e); stop(1); });
service.on('exit', code => stop(code ?? 1)); vite.on('exit', code => stop(code ?? 1));
process.on('SIGINT', () => stop()); process.on('SIGTERM', () => stop());
