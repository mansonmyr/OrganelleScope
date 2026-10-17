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
        assert get('/api/images')==[]
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
        bounds={'x0':0,'x1':7,'y0':0,'y1':7,'z0':0,'z1':2}
        report=post('/api/images/'+image['id']+'/cuboid',json.dumps(bounds).encode());assert report['voxel_count']==192
        mask=post('/api/images/'+image['id']+'/segmentation',json.dumps({**bounds,'method':'manual','threshold':10,'min_voxels':1}).encode());assert mask['foreground_voxels']==9

        print(json.dumps({'frozen_service':'passed','health':get('/health'),'checks':['TIFF import','cuboid','segmentation','removed restoration API returns 404']}))
    finally:
        p.terminate()
        try:p.wait(10)
        except subprocess.TimeoutExpired:p.kill();p.wait()
