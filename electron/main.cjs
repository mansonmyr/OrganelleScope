const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const { spawn, spawnSync } = require('node:child_process');
const crypto = require('node:crypto');
const path = require('node:path');
const net = require('node:net');
const http = require('node:http');
const fs = require('node:fs');

const smokeTest=process.argv.includes('--organelle-smoke-test');
if(smokeTest&&process.env.ORGANELLESCOPE_SMOKE_DATA)app.setPath('userData',process.env.ORGANELLESCOPE_SMOKE_DATA);
const root = path.resolve(__dirname, '..');
const token = crypto.randomBytes(32).toString('hex');
let backend;
let apiUrl;
let mainWindow;
let quitting = false;

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer(); server.on('error', reject);
    server.listen(0, '127.0.0.1', () => { const port = server.address().port; server.close(() => resolve(port)); });
  });
}
function ready(timeout = 120000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    function poll() {
      if (Date.now() - start > timeout) return reject(new Error('Local image service did not start.'));
      if (backend?.exitCode != null) return reject(new Error('Local image service exited during startup.'));
      const req = http.get(`${apiUrl}/health`, res => { res.resume(); if (res.statusCode === 200) resolve(); else setTimeout(poll, 200); });
      req.setTimeout(1000, () => req.destroy());
      req.on('error', () => setTimeout(poll, 200));
    }
    poll();
  });
}
async function start() {
  const port = await freePort(); apiUrl = `http://127.0.0.1:${port}`;
  const env = { ...process.env, ORGANELLESCOPE_SESSION_TOKEN: token };
  const args = ['--port', String(port), '--data-dir', path.join(app.getPath('userData'), 'images')];
  if (app.isPackaged) {
    env.ORGANELLESCOPE_AUTO_SETUP=process.env.ORGANELLESCOPE_DISABLE_AUTO_SETUP==='1'?'0':'1';
    env.ORGANELLESCOPE_MODEL=path.join(app.getPath('userData'),'assistant','models','gemma-4-12b-it-qat-q4_0.gguf');
    const bundledModel=path.join(process.resourcesPath,'local-ai','model','gemma-4-12b-it-qat-q4_0.gguf');
    const bundledRuntime=path.join(process.resourcesPath,'local-ai','runtime',process.platform==='win32'?'llama-server.exe':'llama-server');
    if(fs.existsSync(bundledModel))env.ORGANELLESCOPE_MODEL=bundledModel;
    if(fs.existsSync(bundledRuntime))env.ORGANELLESCOPE_LLAMA_SERVER=bundledRuntime;
    backend = spawn(path.join(process.resourcesPath, 'backend', process.platform === 'win32' ? 'organellescope-backend.exe' : 'organellescope-backend'), args, { env, stdio: ['ignore','pipe','pipe'] });
  } else {
    const localPython = path.join(root, 'backend', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
    const python = process.env.ORGANELLESCOPE_PYTHON || (fs.existsSync(localPython) ? localPython : process.platform === 'win32' ? 'python' : 'python3');
    env.PYTHONPATH = path.join(root, 'backend');
    backend = spawn(python, ['-m', 'organelle_scope.main', ...args], { env, cwd: root, stdio: ['ignore','pipe','pipe'] });
  }
  backend.on('error', error => { dialog.showErrorBox('Image service unavailable', error.message); app.quit(); });
  backend.stdout.resume();
  backend.stderr.on('data', chunk => console.error(String(chunk)));
  backend.on('exit', code => { if (!quitting && mainWindow) dialog.showErrorBox('Image service stopped', `Restart OrganelleScope. Exit code: ${code}`); });
  await ready();
  ipcMain.handle('organelle:runtime', event => {
    if (!mainWindow || event.sender !== mainWindow.webContents || event.senderFrame !== mainWindow.webContents.mainFrame) throw new Error('Untrusted application frame.');
    return { apiUrl, token };
  });
  await createWindow();
  if(smokeTest){
    const target=process.env.ORGANELLESCOPE_SMOKE_REPORT;
    if(!target)throw new Error('Smoke report path required.');
    const deadline=Date.now()+30000;let renderer;
    do{
      renderer=await mainWindow.webContents.executeJavaScript('({title:document.title,text:document.body.innerText,root:!!document.getElementById("root")})');
      if(renderer.root&&renderer.text.includes('OrganelleScope')&&renderer.text.includes('Open TIFF'))break;
      await new Promise(resolve=>setTimeout(resolve,200));
    }while(Date.now()<deadline);
    if(!renderer?.root||!renderer.text.includes('Open TIFF'))throw new Error('Packaged renderer did not mount its image workflow.');
    const picture=await mainWindow.webContents.capturePage();
    if(picture.isEmpty())throw new Error('Packaged renderer returned an empty capture.');
    fs.mkdirSync(path.dirname(target),{recursive:true});
    fs.writeFileSync(target,JSON.stringify({version:app.getVersion(),platform:process.platform,architecture:process.arch,packaged:app.isPackaged,renderer_mounted:true,renderer_capture_size:picture.getSize(),local_backend_ready:true,automatic_download_disabled_for_test:process.env.ORGANELLESCOPE_DISABLE_AUTO_SETUP==='1',scope:'Native application startup and initial renderer paint; not a human interaction, GPU workload, fresh full-weight download or biological validation.'},null,2));
    app.quit();
  }
}
async function createWindow() {
  mainWindow = new BrowserWindow({ width: 1440, height: 960, minWidth: 950, minHeight: 680,
    title: 'OrganelleScope', backgroundColor: '#001524',
    webPreferences: { preload: path.join(__dirname, 'preload.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true } });
  mainWindow.webContents.setWindowOpenHandler(({url}) => {
    try {
      const target=new URL(url);
      const allowed=['string-db.org','www.string-db.org','version-12-5.string-db.org','www.kegg.jp','rest.kegg.jp','www.genome.jp','openaccess.thecvf.com','careamics.github.io','scikit-image.org','docs.scipy.org','pmc.ncbi.nlm.nih.gov','www.cs.ubc.ca'];
      if(target.protocol==='https:' && !target.username && !target.password && !target.port && allowed.includes(target.hostname))void shell.openExternal(target.href);
    } catch { /* Reject malformed or unapproved external links. */ }
    return {action:'deny'};
  });
  mainWindow.webContents.on('will-navigate', event => event.preventDefault());
  mainWindow.on('closed', () => { mainWindow = null; });
  if (process.env.ORGANELLESCOPE_UI_URL && !app.isPackaged) await mainWindow.loadURL(process.env.ORGANELLESCOPE_UI_URL);
  else await mainWindow.loadFile(path.join(root, 'frontend', 'dist', 'index.html'));
}
if(!app.requestSingleInstanceLock())app.quit();
else app.whenReady().then(start).catch(error => {
  if(smokeTest){console.error(error);quitting=true;backend?.kill();app.exit(1);}
  else{dialog.showErrorBox('Startup failed', error.message);app.quit();}
});
app.on('activate', () => { if (!mainWindow && apiUrl) void createWindow(); });
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('before-quit', () => {
  quitting=true;
  if(process.platform==='win32'&&backend?.pid&&backend.exitCode===null){
    // Terminate only this app's owned backend/model tree; do not leave a CPU model orphaned.
    spawnSync(path.join(process.env.SystemRoot||'C:/Windows','System32','taskkill.exe'),['/PID',String(backend.pid),'/T','/F'],{windowsHide:true,stdio:'ignore',timeout:10000});
  }else backend?.kill();
});
