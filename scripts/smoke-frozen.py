"""Start the packaged service and exercise authenticated numeric analysis offline."""
import io,json,os,socket,subprocess,tempfile,time,urllib.request,urllib.error,sys
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
        assert get('/api/ready')['status']=='ok'
        assert get('/api/images')==[]
        assert get('/api/projects')==[] and get('/api/batch/sessions')==[] and get('/api/batch/runs')==[] and get('/api/recovery') is None
        try:get('/api/restoration/status')
        except urllib.error.HTTPError as error:assert error.code==404
        else:raise AssertionError('Removed restoration API is still exposed.')
        import numpy as np,tifffile
        pixels=np.zeros((2,3,8,8),np.uint16);pixels[:,1,2:5,2:5]=100
        tiff=io.BytesIO();tifffile.imwrite(tiff,pixels,ome=True,photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':.5})
        boundary='OrganelleScope-frozen-smoke'
        payload=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="smoke.tif"\r\nContent-Type: image/tiff\r\n\r\n'.encode()+tiff.getvalue()+f'\r\n--{boundary}--\r\n'.encode())
        def post(path,body,content='application/json'):
            with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=body,headers={'X-Session-Token':'frozen-smoke','Content-Type':content}),timeout=120) as response:return json.load(response)
        image=post('/api/images',payload,'multipart/form-data; boundary='+boundary)
        # New asynchronous route is exercised in both frozen platform builds.
        job=post('/api/images/'+image['id']+'/analysis-jobs',json.dumps({'rois':[{'id':'review','kind':'circle','z':1,'points':[{'x':3,'y':3},{'x':4,'y':3}]}],'threshold_mode':'zero'}).encode())
        for _ in range(200):
            status=get('/api/analysis-jobs/'+job['id'])
            if status['status'] not in ('running','cancelling'):break
            time.sleep(.02)
        assert status['status']=='completed' and status['progress']['completed']==status['progress']['total']
        context={'image_id':image['id'],'expected_image_info':image['info'],'state':{'core':{'areas':status['result']['request']['rois'],'analysis':status['result']},'workspaces':{}}}
        with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}/api/images/'+image['id']+'/review-report',data=json.dumps(context).encode(),headers={'X-Session-Token':'frozen-smoke','Content-Type':'application/json'}),timeout=30) as response:
            html=response.read();assert b'data:image/png;base64,' in html and b'href="#roi-0"' in html

        base='/api/images/'+image['id']
        renamed=post(base+'/channels',json.dumps({'labels':['Synthetic A','Synthetic B'],'expected_image_info':image['info']}).encode())
        assert renamed['sha256']==image['sha256'] and renamed['info']['channel_labels']==['Synthetic A','Synthetic B']
        quality=get(base+'/quality?z=1');assert quality['channels'][0]['max']==100 and quality['channels'][0]['storage_ceiling_pixels']==0
        specified=get(base+'/quality?z=1&lateral_resolution_um=0.5&axial_resolution_um=0.6&detector_ceiling=100')
        assert specified['channels'][0]['at_or_above_declared_ceiling_pixels']==9
        assert specified['sampling_review']['axes'][0]['samples_per_declared_resolution']==5
        from PIL import Image
        def png(path):
            with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}'+path,headers={'X-Session-Token':'frozen-smoke'}),timeout=10) as response:return np.asarray(Image.open(io.BytesIO(response.read())))
        assert png(base+'/preview?z=1').max()==0  # native 16-bit values below one display step
        assert png(base+'/preview?z=1&contrast=auto').max()>0
        bounds={'x0':0,'x1':7,'y0':0,'y1':7,'z0':0,'z1':2}
        report=post('/api/images/'+image['id']+'/cuboid',json.dumps(bounds).encode());assert report['voxel_count']==192
        mask=post('/api/images/'+image['id']+'/segmentation',json.dumps({**bounds,'method':'manual','threshold':10,'min_voxels':1}).encode());assert mask['foreground_voxels']==9

        analysis=post(base+'/analysis',json.dumps({'rois':[{'id':'test-roi','kind':'circle','z':1,'points':[{'x':3,'y':3},{'x':5,'y':3}]}],'threshold_mode':'zero'}).encode())
        sweep=post(base+'/validation/parameter-sweep',json.dumps({'rois':[analysis['results'][0]['roi']],'threshold_mode':'zero','threshold_step':10}).encode())
        assert len(sweep['results'][0]['variants'])==7
        volume_sweep=post(base+'/segmentation/sensitivity',json.dumps({**bounds,'method':'manual','threshold':10,'min_voxels':1,'reference_channel':1,'reference_threshold':10,'threshold_step':5}).encode())
        assert len(volume_sweep['variants'])==7 and volume_sweep['variants'][0]['foreground_voxels']==9
        pair=analysis['results'][0]['pairs'][0];assert abs(pair['pcc']-1)<1e-12
        saved=post('/api/projects',json.dumps({'name':'Native round-trip','image_id':image['id'],'expected_image_info':renamed['info'],'state':{'core':{'analysis':analysis},'workspaces':{}}}).encode())
        restored=get('/api/projects/'+saved['id']);assert restored['state']['core']['analysis']==analysis and restored['image']['sha256']==image['sha256']
        notes=post('/api/assistant/notes',json.dumps({'message':'Show recorded analysis summary','context':{'image_id':image['id'],'expected_image_info':renamed['info'],'state':{'core':{'analysis':analysis},'workspaces':{}}}}).encode())
        assert notes['response_mode']=='application_summary' and notes['model'] is None and notes['recorded_quantities']

        print(json.dumps({'frozen_service' :'passed','health':get('/health'),'checks':['authenticated readiness','ROI reference correlation','project save/reopen with source identity','model-free analysis summary','TIFF import','channel labels and source identity','selected-plane signal checks','declared-resolution and ceiling checks','ROI and cuboid sensitivity sweeps','native and optional automatic contrast','cuboid','segmentation','removed restoration API returns 404']}))
    finally:
        p.terminate()
        try:p.wait(10)
        except subprocess.TimeoutExpired:p.kill();p.wait()
