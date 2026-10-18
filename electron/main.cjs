const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const { spawn, spawnSync } = require('node:child_process');
const crypto = require('node:crypto');
const path = require('node:path');
const net = require('node:net');
const http = require('node:http');
const fs = require('node:fs');
const {startupLog, waitForBackend, stopBackend} = require('./lifecycle.cjs');

const smokeTest=process.argv.includes('--organelle-smoke-test');
if(smokeTest&&process.env.ORGANELLESCOPE_SMOKE_DATA)app.setPath('userData',process.env.ORGANELLESCOPE_SMOKE_DATA);
const root = path.resolve(__dirname, '..');
const token = crypto.randomBytes(32).toString('hex');
let backend;
let apiUrl;
let mainWindow;
let quitting = false;
let shutdownComplete = false;
let serviceReady = false;
const diagnostics = startupLog(path.join(app.getPath('userData'), 'logs'), {version:app.getVersion(),platform:process.platform,architecture:process.arch}, [token]);
diagnostics.write('launch');

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer(); server.on('error', reject);
    server.listen(0, '127.0.0.1', () => { const port = server.address().port; server.close(() => resolve(port)); });
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
  backend.on('error', error => diagnostics.write('backend-spawn-error',{message:error.message}));
  backend.stdout.resume();
  backend.stderr.on('data', chunk => {if(!serviceReady)diagnostics.write('backend-startup-output',{message:String(chunk).slice(-3000)});console.error(String(chunk));});
  backend.on('exit', (code,signal) => { diagnostics.write('backend-exit',{code,signal,expected:quitting}); if (!quitting && mainWindow) dialog.showErrorBox('Image service stopped', `Restart OrganelleScope. Exit code: ${code}`); });
  diagnostics.write('backend-spawned');
  await waitForBackend({url:apiUrl,token,child:backend,expectedVersion:app.getVersion()});
  serviceReady=true;diagnostics.write('backend-ready');
  ipcMain.handle('organelle:runtime', event => {
    if (!mainWindow || event.sender !== mainWindow.webContents || event.senderFrame !== mainWindow.webContents.mainFrame) throw new Error('Untrusted application frame.');
    return { apiUrl, token };
  });
  await createWindow();
  diagnostics.write('window-loaded');
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
    const initialLists=await Promise.all(['/api/images','/api/projects'].map(async route=>{
      const response=await fetch(apiUrl+route,{headers:{'X-Session-Token':token}});
      if(!response.ok)throw new Error('Cannot verify initial research storage.');
      return response.json();
    }));
    if(initialLists.some(items=>!Array.isArray(items)||items.length!==0))throw new Error('Isolated installation contains imported images or saved projects.');
    const picture=await mainWindow.webContents.capturePage();
    if(picture.isEmpty())throw new Error('Packaged renderer returned an empty capture.');
    fs.mkdirSync(path.dirname(target),{recursive:true});
    fs.writeFileSync(target,JSON.stringify({version:app.getVersion(),platform:process.platform,architecture:process.arch,packaged:app.isPackaged,renderer_mounted:true,empty_initial_images:true,empty_initial_projects:true,renderer_capture_size:picture.getSize(),diagnostics_available:fs.existsSync(diagnostics.file),local_backend_ready:true,automatic_download_disabled_for_test:process.env.ORGANELLESCOPE_DISABLE_AUTO_SETUP==='1',scope:'Native application startup and initial renderer paint; not a human interaction, GPU workload, fresh full-weight download or biological validation.'},null,2));
    app.quit();
  }
}
async function createWindow() {
  mainWindow = new BrowserWindow({ width: 1440, height: 960, minWidth: 950, minHeight: 680,
    title: 'OrganelleScope', backgroundColor: '#001524',
    webPreferences: { preload: path.join(__dirname, 'preload.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true } });
  mainWindow.webContents.on('render-process-gone',(_event,details)=>{diagnostics.write('renderer-stopped',{reason:details.reason,exitCode:details.exitCode});if(!quitting&&!smokeTest)dialog.showErrorBox('Image workspace stopped','Restart OrganelleScope. Saved projects and source images remain on disk. Diagnostic log: '+diagnostics.file);});
  mainWindow.webContents.on('preload-error',(_event,_file,error)=>diagnostics.write('preload-error',{message:error.message}));
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
async function shutdown() {
  quitting=true;
  await stopBackend(backend, {terminateTree:process.platform==='win32' ? pid=>spawnSync(path.join(process.env.SystemRoot||'C:/Windows','System32','taskkill.exe'),['/PID',String(pid),'/T','/F'],{windowsHide:true,stdio:'ignore',timeout:10000}) : undefined});
  shutdownComplete=true;diagnostics.write('shutdown-complete');
}
async function startupFailure(error) {
  diagnostics.write('startup-failed',{message:error.message,stack:error.stack?.slice(-3000)});
  if(!smokeTest)dialog.showErrorBox('Startup failed',error.message+'\nDiagnostic log: '+diagnostics.file);
  else console.error(error);
  await shutdown();app.exit(1);
}
if(!app.requestSingleInstanceLock())app.quit();
else app.whenReady().then(start).catch(startupFailure);
app.on('second-instance',()=>{if(mainWindow){if(mainWindow.isMinimized())mainWindow.restore();mainWindow.focus();}});
app.on('activate', () => { if (!quitting && !mainWindow && apiUrl) void createWindow().catch(startupFailure); });
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('before-quit', event => {
  if(shutdownComplete || !backend){quitting=true;return;}
  event.preventDefault();
  if(!quitting)void shutdown().then(()=>app.quit());
});
