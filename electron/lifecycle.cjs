const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

function startupLog(directory, metadata, secrets = []) {
  const file = path.join(directory, 'startup.jsonl');
  function write(event, details = {}) {
    try {
      fs.mkdirSync(directory, { recursive: true });
      if (fs.existsSync(file) && fs.statSync(file).size > 1024 * 1024) {
        fs.rmSync(file + '.1', { force: true }); fs.renameSync(file, file + '.1');
      }
      let line = JSON.stringify({ utc: new Date().toISOString(), ...metadata, event, ...details });
      for (const secret of secrets) if (secret) line = line.split(secret).join('[redacted]');
      if(line.length>16000)line=JSON.stringify({...metadata,event,truncated:true,message:line.slice(0,12000)});
      fs.appendFileSync(file, line + '\n');
    } catch { /* Diagnostic storage must never prevent the analysis application opening. */ }
  }
  return { file, write };
}

function waitForBackend({ url, token, child, expectedVersion, timeout = 120000, interval = 200 }) {
  return new Promise((resolve, reject) => {
    let request, poll, deadline, finished = false;
    function finish(error) {
      if (finished) return;
      finished = true; clearTimeout(poll); clearTimeout(deadline);
      child?.removeListener('exit', exited); child?.removeListener('error', failed);
      request?.destroy(); error ? reject(error) : resolve();
    }
    const exited = (code, signal) => finish(new Error(`Image service exited during startup (${code ?? signal}).`));
    const failed = error => finish(new Error(`Image service could not start: ${error.message}`));
    child?.once('exit', exited); child?.once('error', failed);
    if (child && (child.exitCode != null || child.signalCode != null)) return exited(child.exitCode, child.signalCode);
    deadline = setTimeout(() => finish(new Error('Image service did not become ready before the startup deadline.')), timeout);
    function retry() { if (!finished) poll = setTimeout(check, interval); }
    function check() {
      if (finished) return;
      request = http.get(url + '/api/ready', { headers: { 'X-Session-Token': token } }, response => {
        let body = '';
        response.on('data', chunk => { if (body.length < 4096) body += chunk.toString(); });
        response.on('error', retry);
        response.on('end', () => {
          if (finished) return;
          try { const info=JSON.parse(body); if (response.statusCode === 200 && info.status === 'ok' && info.service === 'OrganelleScope' && typeof info.version === 'string' && (!expectedVersion || info.version.replace(/\.dev\d+$/,'')===expectedVersion)) return finish(); } catch {}
          retry();
        });
      });
      request.setTimeout(1000, () => request.destroy());
      request.on('error', retry);
    }
    check();
  });
}

function stopBackend(child, { timeout = 8000, terminateTree } = {}) {
  if (!child || child.exitCode != null || child.signalCode != null) return Promise.resolve();
  return new Promise(resolve => {
    let timer;
    const done = () => { clearTimeout(timer); child.removeListener('exit', done); resolve(); };
    child.once('exit', done);
    timer = setTimeout(() => { try { child.kill('SIGKILL'); } catch {} done(); }, timeout);
    try { terminateTree ? terminateTree(child.pid) : child.kill('SIGTERM'); } catch { done(); }
  });
}
module.exports = { startupLog, waitForBackend, stopBackend };
