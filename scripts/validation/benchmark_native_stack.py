"""Native frozen-service workload: synthetic 16-bit, four-channel, 2048-square stack.
Uses a disposable source/store; exact cuboid sums are checked independently.
"""
import argparse,contextlib,hashlib,json,os,socket,subprocess,sys,tempfile,threading,time
from pathlib import Path
import httpx,numpy as np,psutil,tifffile

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--slices',type=int,choices=[8,16,32],default=16);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
root=Path(__file__).resolve().parents[2];binary=root/'backend/dist/organellescope-backend'/('organellescope-backend.exe' if sys.platform=='win32' else 'organellescope-backend')
temporary=tempfile.TemporaryDirectory(prefix="OrganelleScope-native-stack-");directory=temporary.name;log=None
measure={'peak_process_tree_rss_bytes':0,'minimum_system_available_bytes':psutil.virtual_memory().available};done=threading.Event()
def monitor():
 process=psutil.Process()
 while not done.wait(.05):
  total=0
  for child in [process,*process.children(recursive=True)]:
   try:total+=child.memory_info().rss
   except (psutil.NoSuchProcess,psutil.AccessDenied):pass
  measure['peak_process_tree_rss_bytes']=max(measure['peak_process_tree_rss_bytes'],total)
  measure['minimum_system_available_bytes']=min(measure['minimum_system_available_bytes'],psutil.virtual_memory().available)
thread=threading.Thread(target=monitor,daemon=True);thread.start();timings={};server=None
try:
 if True:
  temp=Path(directory);source=temp/'synthetic.tif';yy,xx=np.mgrid[:2048,:2048];base=(100+300*np.exp(-((xx-1024)**2+(yy-1024)**2)/20000)).astype('uint16');del yy,xx
  def planes():
   for c in range(4):
    for z in range(args.slices):yield base+c*100+z*5
  tifffile.imwrite(source,planes(),shape=(4,args.slices,2048,2048),dtype='uint16',ome=True,photometric='minisblack',compression='deflate',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':8/args.slices})
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  log=(temp/'service.log').open('w');server=subprocess.Popen([str(binary),'--port',str(port),'--data-dir',str(temp/'images')],env={**os.environ,'ORGANELLESCOPE_SESSION_TOKEN':'native-workload','ORGANELLESCOPE_AUTO_SETUP':'0'},stdout=log,stderr=log)
  with httpx.Client(base_url=f'http://127.0.0.1:{port}',headers={'X-Session-Token':'native-workload'},timeout=300) as client:
   deadline=time.monotonic()+120
   while True:
    try:
     if client.get('/health').status_code==200:break
    except httpx.HTTPError:pass
    if time.monotonic()>deadline:raise RuntimeError('Frozen service failed to start')
    time.sleep(.2)
   def timed(name,fn):
    start=time.monotonic();response=fn();response.raise_for_status();timings[name]=time.monotonic()-start;return response
   with source.open('rb') as stream:record=timed('upload_and_inspection_seconds',lambda:client.post('/api/images',files={'file':('synthetic.tif',stream)})).json()
   url='/api/images/'+record['id'];bounds={'x0':992,'x1':1055,'y0':992,'y1':1055,'z0':0,'z1':args.slices-1}
   volume=timed('volume_seconds',lambda:client.get(url+'/volume?channel=0&units=physical'));del volume
   cube=timed('cuboid_seconds',lambda:client.post(url+'/cuboid',json=bounds)).json()
   assert cube['voxel_count']==64*64*args.slices
   for c in range(4):
    expected=sum(float((base[992:1056,992:1056]+c*100+z*5).sum(dtype='float64')) for z in range(args.slices))
    assert cube['channels'][c]['sum']==expected
   timed('segmentation_seconds',lambda:client.post(url+'/segmentation',json={**bounds,'threshold':300,'method':'manual','min_voxels':8}))
   qc=timed('full_plane_qc_seconds',lambda:client.post(url+'/processing/diagnostics?z=0',json={'background':'constant','offsets':[100,200,300,400]})).json()
   assert all(c['changed_pixels']==2048**2 for c in qc['channels'])
   # Three identical imports are deliberate technical repeats, never independent experiments.
   batch_items=[]
   for index in range(3):
    if index==0: image=record
    else:
     with source.open('rb') as stream:image=client.post('/api/images',files={'file':('technical-copy.tif',stream)}).json()
    batch_items.append({'image_id':image['id'],'reviewed':True,'condition':'synthetic','experiment':'one-technical-source','cell':'same-source','analysis':{'rois':[{'id':'center','kind':'circle','z':args.slices//2,'points':[{'x':1024,'y':1024},{'x':1040,'y':1024}]}],'threshold_mode':'zero'}})
   def batch_run():
    saved=client.post('/api/batch/sessions',json={'name':'Synthetic sequential workload','items':batch_items});saved.raise_for_status();saved=saved.json()
    response=client.post('/api/batch/runs',json={'session_id':saved['id'],'revision':saved['revision']});response.raise_for_status();ident=response.json()['id'];deadline=time.monotonic()+120
    while True:
     response=client.get('/api/batch/runs/'+ident);response.raise_for_status()
     if response.json()['status']!='running':return response
     if time.monotonic()>deadline:raise RuntimeError('Native batch workload timed out')
     time.sleep(.05)
   batch=timed('three_image_sequential_batch_seconds',batch_run).json()
   assert batch['status']=='completed'
   assert len(batch['design_review']['repeated_sources'])==1
   yy,xx=np.mgrid[:2048,:2048];mask=(xx-1024)**2+(yy-1024)**2<=16**2;del yy,xx
   for item in batch['items']:
    result=item['result']['results'][0];assert result['pixel_count']==int(mask.sum())
    for c in range(4):assert result['channel_summary'][c]['sum']==float((base[mask]+c*100+(args.slices//2)*5).sum(dtype='float64'))
   report={'batch_images_checked':3,'batch_all_channel_sums_exact':True,'technical_repeated_source_flagged':True,'shape_czyx' :[4,args.slices,2048,2048],'decoded_bytes':4*args.slices*2048**2*2,'z_depth_um':8,'native_service_health':client.get('/health').json(),'platform':sys.platform,'timings':timings,'memory':measure,'all_four_cuboid_sums_exact':True,'scope':'One deterministic compressed synthetic stack through a native frozen executable, including multipart upload. Process-tree RSS includes the driver and service, not unrelated applications. This is not a realistic acquisition distribution, sustained batch benchmark, human usability assessment or biological validation.'}
finally:
 if server:
  server.terminate()
  try:server.wait(5)
  except subprocess.TimeoutExpired:server.kill();server.wait(5)
 if log:log.close()
 temporary.cleanup()
 done.set();thread.join(1)
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
