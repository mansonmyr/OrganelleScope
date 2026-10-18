import hashlib,io
from pathlib import Path
from types import SimpleNamespace
from organelle_scope.model_setup import ModelSetup

class Response(io.BytesIO):
 def __init__(self,data,status=200,headers=None):super().__init__(data);self.status=status;self.headers=headers or {}
 def geturl(self):return 'https://huggingface.co/test'
class Opener:
 def __init__(self,response):self.response=response;self.requests=[]
 def open(self,request,timeout):self.requests.append(request);return self.response

def fixture(tmp_path,data=b'valid model'):
 binary=tmp_path/'llama-server';binary.write_bytes(b'test')
 path=tmp_path/'models/gemma.gguf'
 manifest={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'quantization':'https://huggingface.co/google/test','revision':'pinned','filename':'gemma.gguf'}
 return SimpleNamespace(model=path,binary=binary,manifest=manifest,status=lambda:{'model_available':path.is_file() and path.stat().st_size==len(data)})

def finish(setup):setup.start();setup.thread.join(5);assert not setup.thread.is_alive();return setup.status()

def test_verified_download_atomic_install(tmp_path):
 model=fixture(tmp_path);setup=ModelSetup(model,opener=Opener(Response(b'valid model')))
 assert finish(setup)['phase']=='complete';assert model.model.read_bytes()==b'valid model'
 assert not model.model.with_suffix('.gguf.part').exists()

def test_resume_exact_pinned_range(tmp_path):
 model=fixture(tmp_path);model.model.parent.mkdir();model.model.with_suffix('.gguf.part').write_bytes(b'valid ')
 opener=Opener(Response(b'model',206,{'Content-Range':'bytes 6-10/11'}));setup=ModelSetup(model,opener=opener)
 assert finish(setup)['phase']=='complete';assert opener.requests[0].get_header('Range')=='bytes=6-'

def test_server_without_range_support_restarts_safely(tmp_path):
 model=fixture(tmp_path);model.model.parent.mkdir();model.model.with_suffix('.gguf.part').write_bytes(b'valid ')
 assert finish(ModelSetup(model,opener=Opener(Response(b'valid model'))))['phase']=='complete'
 assert model.model.read_bytes()==b'valid model'

def test_corrupted_download_is_never_installed(tmp_path):
 model=fixture(tmp_path);state=finish(ModelSetup(model,opener=Opener(Response(b'wrong model'))))
 assert state['phase']=='error';assert not model.model.exists();assert not model.model.with_suffix('.gguf.part').exists()

def test_incorrect_resumed_range_is_rejected(tmp_path):
 model=fixture(tmp_path);state=finish(ModelSetup(model,opener=Opener(Response(b'valid model',206,{'Content-Range':'bytes 2-10/11'}))))
 assert state['phase']=='error';assert not model.model.exists()

def test_interrupted_download_retains_resumable_partial(tmp_path):
 model=fixture(tmp_path);setup=ModelSetup(model,opener=Opener(Response(b'valid ')))
 assert finish(setup)['phase']=='error';assert model.model.with_suffix('.gguf.part').read_bytes()==b'valid '

def test_paused_install_remains_paused_on_next_launch(tmp_path):
 model=fixture(tmp_path);setup=ModelSetup(model,opener=Opener(Response(b'valid model')))
 setup.cancelled.set();setup._run();assert setup.status()['phase']=='paused'
 assert ModelSetup(model,automatic=True).status()['phase']=='paused';assert not model.model.exists()


def test_binary_weights_preserve_newlines_and_control_bytes(tmp_path):
 data=bytes([0,10,13,10,26,255,128]);model=fixture(tmp_path,data)
 assert finish(ModelSetup(model,opener=Opener(Response(data))))['phase']=='complete'
 assert model.model.read_bytes()==data


def test_completed_weights_do_not_show_setup_again_on_relaunch(tmp_path):
 model=fixture(tmp_path);model.model.parent.mkdir();model.model.write_bytes(b'valid model')
 assert ModelSetup(model,automatic=True).status()['phase']=='complete'

def test_app_exit_allows_automatic_resume_but_explicit_pause_does_not(tmp_path):
 model=fixture(tmp_path);setup=ModelSetup(model,automatic=True,opener=Opener(Response(b'valid model')))
 setup.closed=True;setup.cancelled.set();setup._run()
 assert ModelSetup(model,automatic=True).status()['phase']=='idle'
