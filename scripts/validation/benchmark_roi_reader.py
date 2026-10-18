"""Bounded synthetic stack: isolated-process reader timing, memory and exact parity."""
import argparse,hashlib,json,os,subprocess,tempfile,threading,time
from pathlib import Path
import numpy as np
import psutil
import tifffile
from organelle_scope.image_io import inspect_tiff
from organelle_scope.roi_analysis import AnalysisRequest
import organelle_scope.analysis_service as service


def worker(folder,mode):
    info=inspect_tiff(folder/'source.tiff');info.filename='synthetic-stack.tif'
    record={'id':'synthetic','sha256':'synthetic','info':info.model_dump()}
    options=AnalysisRequest(rois=[{'id':str(z),'kind':'circle','z':z,'points':[{'x':512,'y':512},{'x':532,'y':512}]} for z in range(8)],threshold_mode='zero')
    real=service.read_plane
    if mode=='per-plane-open':
        def prior(*a,**kw):kw.pop('tiff',None);return real(*a,**kw)
        service.read_plane=prior
    process=psutil.Process();peak=[process.memory_info().rss];stop=threading.Event()
    def monitor():
        while not stop.wait(.01):peak[0]=max(peak[0],process.memory_info().rss)
    thread=threading.Thread(target=monitor,daemon=True);thread.start();start=time.perf_counter()
    result=service.compute_analysis(folder,record,info,options)
    elapsed=time.perf_counter()-start;stop.set();thread.join()
    return {'mode':mode,'seconds':elapsed,'peak_sampled_rss_bytes':peak[0],'result_sha256':hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest(),'roi_count':len(result['results'])}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--worker',type=Path);p.add_argument('--mode');p.add_argument('--output',type=Path);args=p.parse_args()
    if args.worker:print(json.dumps(worker(args.worker,args.mode)));return
    if args.output is None:p.error('--output is required')
    with tempfile.TemporaryDirectory(prefix='OrganelleScope-roi-reader-') as directory:
        folder=Path(directory);yy,xx=np.mgrid[:1024,:1024];base=((xx+yy)%4096).astype('uint16');del xx,yy
        tifffile.imwrite(folder/'source.tiff',(base+c*100+z for c in range(4) for z in range(8)),shape=(4,8,1024,1024),dtype='uint16',ome=True,compression='deflate',photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':.4})
        outputs=[]
        for mode in ['per-plane-open','shared-directory','shared-directory','per-plane-open']:
            run=subprocess.run([os.sys.executable,__file__,'--worker',str(folder),'--mode',mode],capture_output=True,text=True,check=True)
            outputs.append(json.loads(run.stdout))
        assert len({r['result_sha256'] for r in outputs})==1
        report={'scope':'Synthetic four-channel, eight-slice, 1024-square uint16 deflate TIFF (64 MiB decoded); eight XY ROIs. Separate processes, two runs per mode in alternating order. OS page-cache effects remain; timings are observations, not a universal speed guarantee. Peak RSS sampled every 10 ms. Temporary source removed after measurement.','numerical_parity':True,'runs':outputs}
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
