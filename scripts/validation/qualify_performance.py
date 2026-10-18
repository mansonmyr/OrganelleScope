"""Isolated HTTP workloads on private TIFFs and synthetic stacks; no cloud upload.
Private details stay in --private-output. --public-output contains only aggregate
engineering measurements. Technical copies never create biological replication.
"""
import argparse,hashlib,io,json,os,platform,socket,subprocess,sys,tempfile,threading,time
from pathlib import Path
import httpx,numpy as np,psutil,tifffile
from PIL import Image
from scipy.stats import pearsonr


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--real-dir',type=Path);p.add_argument('--batch-size',type=int,default=30)
    p.add_argument('--slices',type=int,default=64);p.add_argument('--rss-budget-mib',type=int,default=1024)
    p.add_argument('--private-output',required=True,type=Path);p.add_argument('--public-output',type=Path)
    args=p.parse_args()
    if not 1<=args.batch_size<=50 or not 2<=args.slices<=64 or not 256<=args.rss_budget_mib<=4096:p.error('Use 1–50 batch items, 2–64 slices and a 256–4096 MiB RSS budget.')
    if args.private_output.exists() or args.public_output and args.public_output.exists():raise ValueError('Keep prior measurements; choose new output paths.')
    root=Path(__file__).resolve().parents[2]
    report={'scope':'Source-service HTTP workloads on one computer, model unloaded. Real images remain local and unmodified. Test ROIs are geometric regions, not approved biological structures. RSS-supervised budgets do not emulate a computer with less physical RAM, GPU memory or different OS. Technical repeats are not independent acquisitions. Single-session timings include warm OS caches.','host':{'platform':platform.platform(),'physical_memory_bytes':psutil.virtual_memory().total},'rss_budget_mib':args.rss_budget_mib,'memory':{'service_peak_rss_bytes':0,'driver_peak_rss_bytes':0},'implementation_sha256':{name:hashlib.sha256((root/'backend/organelle_scope'/name).read_bytes()).hexdigest() for name in ('main.py','image_io.py','analysis_service.py')},'cases':[],'batch':None,'source_files_unchanged':False}
    source_paths=sorted(args.real_dir.glob('*.tif')) if args.real_dir else []
    initial={str(path):digest(path) for path in source_paths}
    stop=threading.Event();exceeded=threading.Event();server=None;monitor=None
    def save():
        args.private_output.parent.mkdir(parents=True,exist_ok=True);args.private_output.write_text(json.dumps(report,indent=2)+'\n')
    save()
    try:
        with tempfile.TemporaryDirectory(prefix='OrganelleScope-performance-') as temporary:
            temp=Path(temporary);source=temp/'synthetic.tif';yy,xx=np.mgrid[:2048,:2048];base=((xx+yy)%2048).astype('uint16');del xx,yy
            tifffile.imwrite(source,(base+c*100+z for c in range(4) for z in range(args.slices)),shape=(4,args.slices,2048,2048),dtype='uint16',ome=True,photometric='minisblack',compression='deflate',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':.4})
            with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
            with (temp/'service.log').open('w') as log:
                server=subprocess.Popen([sys.executable,'-m','organelle_scope.main','--port',str(port),'--data-dir',str(temp/'profile/images')],cwd=root,env={**os.environ,'PYTHONPATH':str(root/'backend'),'ORGANELLESCOPE_SESSION_TOKEN':'performance-local','ORGANELLESCOPE_AUTO_SETUP':'0','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'},stdout=log,stderr=log)
                service=psutil.Process(server.pid);driver=psutil.Process()
                def measure():
                    while not stop.wait(.02):
                        try:
                            rss=service.memory_info().rss;report['memory']['service_peak_rss_bytes']=max(report['memory']['service_peak_rss_bytes'],rss)
                            report['memory']['driver_peak_rss_bytes']=max(report['memory']['driver_peak_rss_bytes'],driver.memory_info().rss)
                            if rss>args.rss_budget_mib*1024**2:exceeded.set();server.terminate();return
                        except psutil.NoSuchProcess:return
                monitor=threading.Thread(target=measure,daemon=True);monitor.start()
                with httpx.Client(base_url=f'http://127.0.0.1:{port}',headers={'X-Session-Token':'performance-local'},timeout=300,trust_env=False) as client:
                    deadline=time.monotonic()+90
                    while True:
                        try:
                            if client.get('/api/ready').status_code==200:break
                        except httpx.HTTPError:pass
                        if time.monotonic()>deadline or server.poll() is not None:raise RuntimeError('Service startup failed.')
                        time.sleep(.1)
                    report['service']=client.get('/health').json()
                    def timed(entry,name,fn):
                        began=time.perf_counter();response=fn();response.raise_for_status();entry[name]=time.perf_counter()-began;return response
                    imported=[]
                    for path in [*source_paths,source]:
                        entry={'kind':'synthetic' if path==source else 'real','filename':path.name,'sha256':digest(path),'timings':{}}
                        print('Start',entry['kind'],path.name,flush=True)
                        with path.open('rb') as stream:image=timed(entry['timings'],'upload_seconds',lambda:client.post('/api/images',files={'file':(path.name,stream)})).json()
                        entry['dimensions']=d=image['info']['dimensions'];entry['decoded_bytes']=image['info']['decoded_bytes'];entry['stored_bytes']=path.stat().st_size
                        url='/api/images/'+image['id'];mid=d['Z']//2;cx,cy=d['X']//2,d['Y']//2
                        preview=timed(entry['timings'],'preview_seconds',lambda:client.get(url+f'/preview?z={mid}'));Image.open(io.BytesIO(preview.content)).verify()
                        if d['Z']>1:
                            volume=timed(entry['timings'],'volume_seconds',lambda:client.get(url+'/volume?channel=0&units=voxel'));shape=json.loads(volume.headers['X-Volume-Shape']);assert len(volume.content)==int(np.prod(shape))*2
                            if path==source:
                                expected=np.stack([(base+z)[::16,::16] for z in range(args.slices)])
                                np.testing.assert_array_equal(np.frombuffer(volume.content,'<u2').reshape(shape),expected)
                            del volume
                        rois=[{'id':f'technical-{z}','kind':'circle','z':z,'points':[{'x':cx,'y':cy},{'x':cx+8,'y':cy}]} for z in sorted({0,mid,d['Z']-1})]
                        options={'rois':rois,'threshold_mode':'zero'}
                        began=time.perf_counter();job=client.post(url+'/analysis-jobs',json=options);job.raise_for_status();ident=job.json()['id'];latencies=[]
                        while True:
                            heartbeat=time.perf_counter();ready=client.get('/api/ready');ready.raise_for_status();latencies.append(time.perf_counter()-heartbeat)
                            result=client.get('/api/analysis-jobs/'+ident);result.raise_for_status();job=result.json()
                            if job['status'] not in ('running','cancelling'):break
                            if time.perf_counter()-began>180:raise RuntimeError('ROI job timed out.')
                            time.sleep(.02)
                        assert job['status']=='completed',job.get('error');entry['timings']['roi_job_seconds']=time.perf_counter()-began
                        entry['maximum_ready_latency_seconds']=max(latencies);entry['ready_probes']=len(latencies)
                        # Independent native-page indexing and local circle equation; no app ROI rasterizer.
                        with tifffile.TiffFile(path) as tf:
                            axes=tf.series[0].axes
                            assert axes in ('ZCYX','CYX','CZYX'),axes
                            for row in job['result']['results']:
                                z=row['roi']['z'];yy,xx=np.mgrid[cy-8:cy+9,cx-8:cx+9];mask=(xx-cx)**2+(yy-cy)**2<=64;samples=[]
                                assert row['pixel_count']==int(mask.sum())
                                for c in range(d['C']):
                                    index=c*d['Z']+z if axes=='CZYX' else z*d['C']+c
                                    values=tf.pages[index].asarray()[cy-8:cy+9,cx-8:cx+9][mask].astype(float);samples.append(values)
                                    assert row['channel_summary'][c]['sum']==float(values.sum())
                                for pair in row['pairs']:
                                    a,b=samples[pair['channel_a']],samples[pair['channel_b']]
                                    expected=float(pearsonr(a,b).statistic) if a.std()>0 and b.std()>0 else None
                                    assert pair['pcc'] is None if expected is None else np.isclose(pair['pcc'],expected,atol=1e-10)
                        entry['independent_roi_counts_sums_pearson_match']=True;report['cases'].append(entry);save();imported.append((path,image,options));print('Pass',entry['kind'],flush=True)
                    smallest=min((row for row in imported if row[0]!=source),key=lambda row:row[0].stat().st_size) if source_paths else imported[-1]
                    path,first,options=smallest;items=[]
                    for n in range(args.batch_size):
                        if n==0:image=first
                        else:
                            with path.open('rb') as stream:response=client.post('/api/images',files={'file':('technical-repeat.tif',stream)});response.raise_for_status();image=response.json()
                        items.append({'image_id':image['id'],'analysis':options,'reviewed':True,'condition':'technical','experiment':'same-source','cell':'same-source'})
                    draft=client.post('/api/batch/sessions',json={'name':'Technical repeated workload','items':items});draft.raise_for_status();draft=draft.json()
                    began=time.perf_counter();run=client.post('/api/batch/runs',json={'session_id':draft['id'],'revision':draft['revision']});run.raise_for_status();ident=run.json()['id'];latencies=[]
                    while True:
                        t=time.perf_counter();client.get('/api/ready').raise_for_status();latencies.append(time.perf_counter()-t)
                        response=client.get('/api/batch/runs/'+ident);response.raise_for_status();run=response.json()
                        if run['status'] not in ('running','cancelling'):break
                        if time.perf_counter()-began>300:raise RuntimeError('Batch timed out.')
                        time.sleep(.05)
                    assert run['status']=='completed' and all(i['status']=='completed' for i in run['items'])
                    assert len(run['design_review']['repeated_sources'])==(1 if args.batch_size>1 else 0)
                    first_result=run['items'][0]['result']['results']
                    assert all(i['result']['results']==first_result for i in run['items'])
                    excel=client.get('/api/batch/runs/'+ident+'/xlsx');excel.raise_for_status()
                    report['batch']={'items':args.batch_size,'elapsed_seconds':time.perf_counter()-began,'all_completed':True,'exact_repeat_results':True,'repeated_source_flagged':True,'maximum_ready_latency_seconds':max(latencies),'ready_probes':len(latencies),'excel_bytes':len(excel.content),'scope':'Repeated imports of one real field, or synthetic data when no real directory supplied. Technical throughput, not biological replication.'};save()
                server.terminate();server.wait(10)
        report['source_files_unchanged']=all(digest(Path(path))==before for path,before in initial.items())
        assert report['source_files_unchanged'];report['status']='passed'
    except Exception as exc:
        report.update(status='failed',error=str(exc),rss_budget_exceeded=exceeded.is_set());raise
    finally:
        stop.set()
        if server and server.poll() is None:
            server.terminate()
            try:server.wait(5)
            except subprocess.TimeoutExpired:server.kill();server.wait(5)
        if monitor:monitor.join(2)
        save()
        if args.public_output:
            safe={k:report.get(k) for k in ('scope','host','service','implementation_sha256','rss_budget_mib','memory','status','rss_budget_exceeded','batch','source_files_unchanged')}
            safe['cases']=[{k:v for k,v in case.items() if k not in ('filename','sha256','dimensions')} for case in report['cases']]
            safe['real_file_count']=len(source_paths)
            args.public_output.parent.mkdir(parents=True,exist_ok=True);args.public_output.write_text(json.dumps(safe,indent=2)+'\n')
if __name__=='__main__':main()
