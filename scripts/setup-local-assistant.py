"""Explicit, pinned development setup. Downloads are never triggered by opening the app."""
import argparse,hashlib,json,platform,ssl,sys,tarfile,urllib.request,zipfile
from pathlib import Path
import certifi

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from organelle_scope.local_model import MODEL
RUNTIMES={
 'Darwin-arm64':{'file':'llama-b11669-bin-macos-arm64.tar.gz','sha256':'dbed55493d72bc1ba2babc8770d669c2289b5bc4ee9fb2a4dfc158d45b7d13fd','bytes':12191582},
 'Windows-AMD64':{'file':'llama-b11669-bin-win-cpu-x64.zip','sha256':'37b3efcf962847ca869745fd4ccf7f5e7e8dacfeff9fa3523b4ca8cdc66d632b','bytes':19537886},
}

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def download(url,path,size,digest):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.is_file() and path.stat().st_size==size and sha(path)==digest:
  print('Verified existing',path.name,flush=True);return
 temp=path.with_suffix(path.suffix+'.part');print('Downloading',path.name,f'({size/1e9:.3f} GB)',flush=True)
 request=urllib.request.Request(url,headers={'User-Agent':'OrganelleScope-development-setup'})
 with urllib.request.urlopen(request,timeout=60,context=ssl.create_default_context(cafile=certifi.where())) as response,temp.open('wb') as stream:
  received=0;last=0
  while chunk:=response.read(1024*1024):
   received+=len(chunk)
   if received>size:raise ValueError('Downloaded size exceeds pinned manifest.')
   stream.write(chunk)
   if received-last>=128*1024*1024:print(f'  {received/size:.0%}',flush=True);last=received
 if temp.stat().st_size!=size or sha(temp)!=digest:raise ValueError('Integrity verification failed; incomplete file was not installed.')
 temp.replace(path)

def main():
 parser=argparse.ArgumentParser(description='Install pinned llama.cpp and Qwen3.5-4B for local development (about 2.73 GB download).')
 parser.add_argument('--download',action='store_true',help='Explicitly download and verify the model/runtime.')
 args=parser.parse_args();key=platform.system()+'-'+platform.machine()
 if key not in RUNTIMES:parser.error('Supported setup: Apple Silicon macOS or native Windows x64. Windows ARM/emulation and other targets need separate qualification.')
 runtime=RUNTIMES[key];manifest={'model':MODEL,'runtime':runtime,'runtime_tag':'b11669'}
 print(json.dumps(manifest,indent=2))
 if not args.download:return
 download('https://huggingface.co/lmstudio-community/Qwen3.5-4B-GGUF/resolve/'+MODEL['revision']+'/'+MODEL['filename'],ROOT/'.local-models'/MODEL['filename'],MODEL['bytes'],MODEL['sha256'])
 archive=ROOT/'.local-runtime'/runtime['file']
 download('https://github.com/ggml-org/llama.cpp/releases/download/b11669/'+runtime['file'],archive,runtime['bytes'],runtime['sha256'])
 if key.startswith('Darwin'):
  with tarfile.open(archive) as source:source.extractall(ROOT/'.local-runtime',filter='data')
 else:
  destination=ROOT/'.local-runtime/llama-b11669';destination.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(archive) as source:
   for member in source.infolist():
    target=(destination/member.filename).resolve()
    if not target.is_relative_to(destination.resolve()):raise ValueError('Unsafe archive entry.')
   source.extractall(destination)
 print('Verified local assistant files are ready. Start the app, save a project, then use Local assistant → Start local model.')

if __name__=='__main__':main()
