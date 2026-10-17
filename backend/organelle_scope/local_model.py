"""Owned loopback-only llama.cpp process. No external inference endpoint or API key."""
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from threading import Lock

MODEL={
 'name':'Gemma 4 12B Instruct QAT Q4_0','filename':'gemma-4-12b-it-qat-q4_0.gguf','bytes':6975879296,
 'sha256':'93567e57a8fe10b23569b9d9ec38cd005deedf71e29477c421a4b83f418a538b',
 'upstream':'https://huggingface.co/google/gemma-4-12B-it',
 'quantization':'https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-gguf',
 'revision':'29d097773436b69ff9feafd636ab4cf873786537','license':'Apache-2.0',
 'runtime':'llama.cpp b11669','context_tokens':8192,
 'vision_enabled':False,'thinking_enabled':False,'temperature':1.0,
}


class LocalModel:
 def __init__(self,log_dir,manifest=None):
  self.manifest=dict(MODEL if manifest is None else manifest)
  repository=Path(__file__).resolve().parents[2]
  self.repository=repository;self.cleanup_report=None
  # Packaged deployments supply absolute bundled paths via the desktop launcher.
  self.binary=Path(os.environ.get('ORGANELLESCOPE_LLAMA_SERVER',str(repository/'.local-runtime/llama-b11669'/('llama-server.exe' if sys.platform=='win32' else 'llama-server'))))
  self.model=Path(os.environ.get('ORGANELLESCOPE_MODEL',str(repository/'.local-models'/self.manifest['filename'])))
  self.log_dir=Path(log_dir);self.process=None;self.port=None;self.key=None;self.lock=Lock();self.log=None;self.verified=None
  # Do not inherit proxy settings for localhost model traffic.
  self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))

 def status(self):
  running=self.process is not None and self.process.poll() is None
  ready=False
  if running:
   try:self._request('/health',timeout=1);ready=True
   except (OSError,ValueError):pass
  return {'model':self.manifest,'runtime_available':self.binary.is_file(),'model_available':self.model.is_file() and self.model.stat().st_size==self.manifest['bytes'],
          'running':running,'ready':ready,'verified':self.verified is not None,'inference':'local only','log_name':'local-assistant.log','cleanup':self.cleanup_report}

 def _request(self,path,body=None,timeout=120):
  if self.port is None:raise ValueError('Start the local model first.')
  request=urllib.request.Request(f'http://127.0.0.1:{self.port}'+path,data=json.dumps(body).encode() if body is not None else None,
    headers={'Content-Type':'application/json','Authorization':'Bearer '+str(self.key)})
  try:
   with self.opener.open(request,timeout=timeout) as response:
    raw=response.read(2*1024*1024+1)
    if len(raw)>2*1024*1024:raise ValueError('Local model response exceeded the size limit.')
    return json.loads(raw)
  except urllib.error.HTTPError as exc:
   raise ValueError(f'Local model returned status {exc.code}. Check the local assistant log.') from exc
  except (OSError,ValueError) as exc:
   raise ValueError('Local model unavailable or timed out. Check its status and try again.') from exc

 def start(self):
  with self.lock:
   if self.process is not None and self.process.poll() is None:return self.status()
   if not self.binary.is_file() or not self.model.is_file():raise ValueError('Install the pinned local runtime and model first. See docs/LOCAL_ASSISTANT.md.')
   stamp=(self.model.stat().st_size,self.model.stat().st_mtime_ns)
   if stamp!=self.verified:
    digest=hashlib.sha256()
    with self.model.open('rb') as stream:
     for chunk in iter(lambda:stream.read(4*1024*1024),b''):digest.update(chunk)
    if stamp[0]!=self.manifest['bytes'] or digest.hexdigest()!=self.manifest['sha256']:raise ValueError('Local model integrity check failed. Use the pinned, complete model download.')
    self.verified=stamp
   with socket.socket() as sock:sock.bind(('127.0.0.1',0));self.port=sock.getsockname()[1]
   self.key=secrets.token_urlsafe(32);self.log_dir.mkdir(parents=True,exist_ok=True)
   if self.log:self.log.close()
   self.log=(self.log_dir/'local-assistant.log').open('w')
   args=[str(self.binary),'-m',str(self.model),'--host','127.0.0.1','--port',str(self.port),'--ctx-size',str(self.manifest['context_tokens']),
         '--parallel','1','--jinja','--alias','organellescope-local','--no-webui','--no-slots','--no-warmup','--threads','4','--n-gpu-layers','99']
   # Secret in environment, not command-line arguments or project files.
   environment={**os.environ,'LLAMA_API_KEY':self.key}
   if sys.platform=='win32':args[-1]='0' # CPU baseline until native Windows GPU qualification.
   self.process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=self.log,stderr=self.log,env=environment,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
   return self.status()

 def stop(self):
  with self.lock:
   if self.process and self.process.poll() is None:
    self.process.terminate()
    try:self.process.wait(timeout=5)
    except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=5)
   if self.log:self.log.close();self.log=None
   self.process=None;self.key=None;self.port=None
  return self.status()

 def completion(self,messages,tools=None,response_format=None):
  if not self.status()['ready']:raise ValueError('The local model is not ready. Start it and wait for Ready.')
  body={'model':'organellescope-local','messages':messages,'temperature':self.manifest['temperature'],'top_p':self.manifest.get('top_p',0.95),'top_k':self.manifest.get('top_k',64),'max_tokens':1600,
        'stream':False,'chat_template_kwargs':{'enable_thinking':self.manifest.get('thinking_enabled',False)}}
  if 'repeat_penalty' in self.manifest:body['repeat_penalty']=self.manifest['repeat_penalty']
  if tools:body.update(tools=tools,parallel_tool_calls=False)
  if response_format:body.update(response_format=response_format,max_tokens=1200)
  # Model prefill plus generation can exceed two minutes on a CPU or a busy Mac.
  return self._request('/v1/chat/completions',body,timeout=300)

 def cleanup_after_success(self):
  if self.cleanup_report is None and self.verified is not None and self.process and self.process.poll() is None:
   from organelle_scope.model_storage import cleanup_superseded
   self.cleanup_report=cleanup_superseded(self.repository,self.model)
  return self.cleanup_report
