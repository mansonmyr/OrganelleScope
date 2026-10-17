"""Start the packaged service and exercise authenticated numeric analysis offline."""
import io,json,os,socket,subprocess,tempfile,time,urllib.request,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
exe=Path(os.environ.get('ORGANELLESCOPE_FROZEN_BACKEND',str(root/'backend/dist/organellescope-backend'/('organellescope-backend.exe' if sys.platform=='win32' else 'organellescope-backend'))))
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
with tempfile.TemporaryDirectory(prefix='OrganelleScope-frozen-') as folder:
    p=subprocess.Popen([str(exe),'--port',str(port),'--data-dir',folder],env={**os.environ,'ORGANELLESCOPE_SESSION_TOKEN':'frozen-smoke'},stdout=subprocess.DEVNULL)
    try:
        def get(path):
            with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}'+path,headers={'X-Session-Token':'frozen-smoke'}),timeout=10) as response:return json.load(response)
        for _ in range(300):
            if p.poll() is not None:raise RuntimeError('Frozen backend exited before readiness.')
            try:get('/health');break
            except OSError:time.sleep(.2)
        else:raise RuntimeError('Frozen backend startup timeout.')
        assert get('/api/images')==[]
        import numpy as np,tifffile
        pixels=np.zeros((2,3,8,8),np.uint16);pixels[:,1,2:5,2:5]=100
        tiff=io.BytesIO();tifffile.imwrite(tiff,pixels,ome=True,photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':.5})
        boundary='OrganelleScope-frozen-smoke'
        payload=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="smoke.tif"\r\nContent-Type: image/tiff\r\n\r\n'.encode()+tiff.getvalue()+f'\r\n--{boundary}--\r\n'.encode())
        def post(path,body,content='application/json'):
            with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=body,headers={'X-Session-Token':'frozen-smoke','Content-Type':content}),timeout=120) as response:return json.load(response)
        image=post('/api/images',payload,'multipart/form-data; boundary='+boundary)
        bounds={'x0':0,'x1':7,'y0':0,'y1':7,'z0':0,'z1':2}
        report=post('/api/images/'+image['id']+'/cuboid',json.dumps(bounds).encode());assert report['voxel_count']==192
        mask=post('/api/images/'+image['id']+'/segmentation',json.dumps({**bounds,'method':'manual','threshold':10,'min_voxels':1}).encode());assert mask['foreground_voxels']==9

        status=get('/api/restoration/status')
        if os.environ.get('ORGANELLESCOPE_INCLUDE_RESTORATION')=='1':
            assert status['available'],status
            ids=[]
            for seed in (12,13):
                y,x=np.mgrid[:48,:48];clean=50+200*np.exp(-((x-23)**2+(y-24)**2)/50)
                raw=np.random.default_rng(seed).poisson(clean).astype(np.uint16)
                b=io.BytesIO();tifffile.imwrite(b,raw,ome=True,photometric='minisblack',metadata={'axes':'YX'})
                form=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="n2v.tif"\r\nContent-Type: image/tiff\r\n\r\n'.encode()+b.getvalue()+f'\r\n--{boundary}--\r\n'.encode())
                ids.append(post('/api/images',form,'multipart/form-data; boundary='+boundary)['id'])
            def wait(job):
                for _ in range(240):
                    result=get('/api/restoration/jobs/'+job['id'])
                    if result['status']=='complete':return result
                    if result['status'] in ('failed','cancelled','interrupted'):raise RuntimeError(str(result))
                    time.sleep(.5)
                raise RuntimeError('Frozen restoration job timeout.')
            trained=wait(post('/api/restoration/train',json.dumps({'train_ids':[ids[0]],'validation_ids':[ids[1]],'epochs':1,'steps':1,'patch_size':32,'patches_per_image':8,'filters':8}).encode()))
            inferred=wait(post('/api/restoration/apply',json.dumps({'model_id':trained['model_id'],'image_id':ids[0],'confirm_model_match':True,'tile_size':64,'overlap':16}).encode()))
            checked=post('/api/images/'+ids[0]+'/processing/diagnostics',json.dumps({'restoration_result_id':inferred['result_id']}).encode());assert checked['channels'][0]['changed_pixels']>0
            status['frozen_training_and_inference']='passed; plumbing only, not image quality validation'
        print(json.dumps({'frozen_service':'passed','restoration':status,'health':get('/health')}))
    finally:
        p.terminate()
        try:p.wait(10)
        except subprocess.TimeoutExpired:p.kill();p.wait()
