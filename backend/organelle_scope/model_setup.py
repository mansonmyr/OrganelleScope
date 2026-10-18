"""Resumable, pinned weight setup. Only model bytes leave the network response;
no image, project, measurement or conversation is sent to the provider.
"""
import hashlib,json,os,shutil,ssl,threading,urllib.request
from pathlib import Path
import certifi
import tempfile

class ModelSetup:
 def __init__(self,model,automatic=False,opener=None):
  self.model=model;self.automatic=automatic;self.closed=False;self.thread=None;self.cancelled=threading.Event();self.lock=threading.Lock()
  self.state={'phase':'idle','received_bytes':0,'total_bytes':model.manifest['bytes'],'error':None}
  self.receipt=model.model.parent/'setup-state.json'
  self.opener=opener or urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
  if self.receipt.is_file():
   try:
    saved=json.loads(self.receipt.read_text(encoding='utf-8'))
    if saved.get('phase') in ('paused','error'):self.state.update(phase=saved['phase'],error=saved.get('error'))
   except (OSError,ValueError):pass
  partial=model.model.with_suffix(model.model.suffix+'.part')
  if partial.is_file() and not partial.is_symlink():self.state['received_bytes']=min(partial.stat().st_size,model.manifest['bytes'])
  if model.status()['model_available']:self.state.update(phase='complete',received_bytes=model.manifest['bytes'],error=None)
 def status(self):
  with self.lock:return {**self.state,'automatic':self.automatic,'runtime_bundled':self.model.binary.is_file()}
 def _update(self,**values):
  with self.lock:self.state.update(values)
 def start(self):
  with self.lock:
   if self.thread and self.thread.is_alive():return dict(self.state)
   if self.model.status()['model_available']:self.state.update(phase='complete');return dict(self.state)
   if not self.model.binary.is_file():raise ValueError('The local runtime is missing. Reinstall OrganelleScope before setting up Gemma.')
   self.cancelled.clear();self.state.update(phase='preparing',error=None)
   self.thread=threading.Thread(target=self._run,name='Gemma-setup',daemon=True);self.thread.start()
   return dict(self.state)
 def pause(self):
  self.cancelled.set()
  return self.status()
 def close(self):
  self.closed=True;self.cancelled.set()
  if self.thread:self.thread.join(timeout=2)
 def _save(self):
  if self.receipt.parent.is_symlink() or self.receipt.is_symlink():return
  with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.receipt.parent,prefix='setup-',suffix='.tmp',delete=False) as stream:
   state=self.status()
   if self.closed and state['phase']=='paused':state['phase']='interrupted'
   stream.write(json.dumps(state));temp=Path(stream.name)
  temp.replace(self.receipt)
 def _check_cancel(self):
  if self.cancelled.is_set():raise InterruptedError('Setup paused. Resume when convenient.')
 def _run(self):
  target=self.model.model;part=target.with_suffix(target.suffix+'.part');manifest=self.model.manifest
  try:
   target.parent.mkdir(parents=True,exist_ok=True)
   if target.parent.is_symlink() or target.is_symlink() or part.is_symlink() or self.receipt.is_symlink():raise ValueError('Gemma setup cannot use symbolic links.')
   offset=part.stat().st_size if part.exists() else 0;total=manifest['bytes']
   if offset>total:part.unlink();raise ValueError('Oversized partial download removed. Retry setup.')
   if shutil.disk_usage(target.parent).free<total-offset+512*1024**2:raise ValueError('Insufficient free disk space for Gemma. Free space and retry setup.')
   if offset<total:
    url=manifest['quantization']+'/resolve/'+manifest['revision']+'/'+manifest['filename']
    if not url.startswith('https://huggingface.co/google/'):raise ValueError('Unapproved model download source.')
    request=urllib.request.Request(url,headers={'User-Agent':'OrganelleScope-model-setup','Accept-Encoding':'identity',**({'Range':f'bytes={offset}-'} if offset else {})})
    self._check_cancel()
    with self.opener.open(request,timeout=20) as response:
     if not response.geturl().startswith('https://'):raise ValueError('Model download must use HTTPS.')
     status=response.status
     if status==206:
      content_range=response.headers.get('Content-Range','')
      if content_range!=f'bytes {offset}-{total-1}/{total}':raise ValueError('Server returned an incorrect resumed range.')
     elif status==200:offset=0
     else:raise ValueError('Unexpected model download response.')
     self._update(phase='downloading',received_bytes=offset)
     flags=os.O_WRONLY|os.O_CREAT|getattr(os,'O_BINARY',0)|(os.O_APPEND if offset else os.O_TRUNC)|getattr(os,'O_NOFOLLOW',0)
     with os.fdopen(os.open(part,flags,0o600),'ab' if offset else 'wb') as stream:
      received=offset
      while True:
       self._check_cancel();chunk=response.read(1024*1024)
       if not chunk:break
       received+=len(chunk)
       if received>total:raise ValueError('Model response exceeded its pinned size.')
       stream.write(chunk);self._update(received_bytes=received)
      stream.flush();os.fsync(stream.fileno())
   self._check_cancel()
   if part.stat().st_size!=total:raise ValueError('Download interrupted. Retry to resume the remaining bytes.')
   self._update(phase='verifying',received_bytes=total);digest=hashlib.sha256()
   with part.open('rb') as stream:
    while chunk:=stream.read(4*1024*1024):self._check_cancel();digest.update(chunk)
   if digest.hexdigest()!=manifest['sha256']:
    part.unlink();raise ValueError('Gemma checksum mismatch. Invalid partial file removed; retry a clean download.')
   self._check_cancel();part.replace(target);self._update(phase='complete',error=None)
  except InterruptedError as exc:self._update(phase='paused',error=str(exc))
  except Exception as exc:self._update(phase='paused' if self.cancelled.is_set() else 'error',error=str(exc))
  finally:
   try:self._save()
   except OSError:pass
