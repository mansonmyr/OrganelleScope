const {test} = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const {EventEmitter} = require('node:events');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const {startupLog, waitForBackend, stopBackend} = require('./lifecycle.cjs');

test('readiness requires authenticated service JSON, not an unrelated HTTP 200', async () => {
 let allowed=false, observed;
 const server=http.createServer((req,res)=>{observed=req.headers['x-session-token'];res.end(allowed?JSON.stringify({status:'ok',service:'OrganelleScope',version:'1.0.0'}):'unrelated service');});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const url='http://127.0.0.1:'+server.address().port;
 try {
  await assert.rejects(waitForBackend({url,token:'secret',timeout:60,interval:5}),/deadline/);
  allowed=true; await assert.rejects(waitForBackend({url,token:'secret',expectedVersion:'different-version',timeout:60,interval:5}),/deadline/); await waitForBackend({url,token:'secret',timeout:300}); assert.equal(observed,'secret');
 } finally {server.closeAllConnections();await new Promise(r=>server.close(r));}
});
test('backend spawn error and exit fail immediately and remove listeners', async () => {
 for(const event of ['error','exit']){
  const child=new EventEmitter();child.exitCode=null;
  const pending=waitForBackend({url:'http://127.0.0.1:1',token:'test',child,timeout:300});
  child.emit(event,event==='error'?new Error('not executable'):2);
  await assert.rejects(pending,/could not start|exited/);assert.equal(child.listenerCount('error'),0);assert.equal(child.listenerCount('exit'),0);
 }
});
test('shutdown waits for owned backend exit and escalates only after timeout', async () => {
 const child=new EventEmitter();child.exitCode=null;const signals=[];
 child.kill=signal=>{signals.push(signal);if(signal==='SIGTERM')setTimeout(()=>child.emit('exit',0),5);};
 await stopBackend(child,{timeout:100});assert.deepEqual(signals,['SIGTERM']);
 const stuck=new EventEmitter();stuck.exitCode=null;stuck.kill=signal=>signals.push(signal);
 await stopBackend(stuck,{timeout:10});assert.deepEqual(signals.slice(1),['SIGTERM','SIGKILL']);
});
test('startup log redacts credentials, rotates bounded files and tolerates unwritable storage', () => {
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'OrganelleScope-log-test-'));
 try {
  const log=startupLog(dir,{version:'test'},['private-token']);log.write('failure',{message:'private-token'});
  assert.ok(!fs.readFileSync(log.file,'utf8').includes('private-token'));
  fs.writeFileSync(log.file,'x'.repeat(1024*1024+1));log.write('ready');assert.ok(fs.existsSync(log.file+'.1'));
  const blocked=path.join(dir,'file');fs.writeFileSync(blocked,'test');assert.doesNotThrow(()=>startupLog(blocked,{}).write('test'));
 } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
