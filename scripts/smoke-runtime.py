"""Check that the bundled inference executable and its native libraries can load."""
import argparse,json,platform,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
root=Path(__file__).resolve().parents[1];binary=args.runtime or root/'.local-runtime/llama-b11669'/('llama-server.exe' if sys.platform=='win32' else 'llama-server')
result=subprocess.run([str(binary.resolve()),'--version'],check=True,capture_output=True,text=True,timeout=30)
report={'platform':sys.platform,'architecture':platform.machine(),'runtime':'llama.cpp b11669','native_executable_load':'passed','version_output':(result.stdout+result.stderr).strip()[-3000:],'scope':'Executable/library loading and version command only; not model inference, GPU/CPU performance or hardware compatibility beyond this host.'}
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
