"""Native 16-bit, 2048², four-channel stack workload; isolated synthetic temporary data."""
import io,json,time,tempfile,resource,sys
from pathlib import Path
import numpy as np,tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from PIL import Image
h={'X-Session-Token':'workload'};timings={}
with tempfile.TemporaryDirectory(prefix='OrganelleScope-stack-check-') as temp:
    root=Path(temp);source=root/'synthetic.tif';y,x=np.mgrid[:2048,:2048];base=(100+300*np.exp(-((x-1024)**2+(y-1024)**2)/20000)).astype(np.uint16);del y,x
    def planes():
        for c in range(4):
            for z in range(16):yield base+c*100+z*5
    tifffile.imwrite(source,planes(),shape=(4,16,2048,2048),dtype=np.uint16,ome=True,photometric='minisblack',compression='deflate',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':.5})
    source_bytes=source.stat().st_size
    with TestClient(create_app(root/'images','workload')) as client:
        t=time.monotonic()
        with source.open('rb') as stream:r=client.post('/api/images',headers=h,files={'file':('synthetic-2048.tif',stream)})
        assert r.status_code==200,r.text
        record=r.json();timings['import_seconds']=time.monotonic()-t;url='/api/images/'+record['id'];assert record['info']['dimensions']=={'C':4,'Z':16,'Y':2048,'X':2048,'T':1}
        t=time.monotonic();volume=client.get(url+'/volume?channel=0&units=physical',headers=h);assert volume.status_code==200;timings['volume_seconds']=time.monotonic()-t
        bounds={'x0':992,'x1':1055,'y0':992,'y1':1055,'z0':0,'z1':15}
        t=time.monotonic();r=client.post(url+'/cuboid',headers=h,json=bounds);assert r.status_code==200,r.text;cube=r.json();timings['cuboid_seconds']=time.monotonic()-t
        expected=sum((base[992:1056,992:1056]+z*5).sum(dtype=np.float64) for z in range(16));assert cube['voxel_count']==65536 and cube['channels'][0]['sum']==expected
        t=time.monotonic();r=client.post(url+'/segmentation',headers=h,json={**bounds,'threshold':300,'method':'manual','min_voxels':8});assert r.status_code==200,r.text;timings['segmentation_seconds']=time.monotonic()-t;assert r.json()['foreground_voxels']>0
        t=time.monotonic();r=client.post(url+'/processing/diagnostics?z=0',headers=h,json={'background':'constant','offsets':[100,200,300,400]});assert r.status_code==200,r.text;timings['full_plane_qc_seconds']=time.monotonic()-t
        assert all(c['changed_pixels']==2048**2 for c in r.json()['channels'])
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report={'shape_czyx':[4,16,2048,2048],'bit_depth':16,'decoded_bytes':4*16*2048**2*2,'compressed_file_bytes':source_bytes,'source_sha256':record['sha256'],'calibration_um_xyz':[.1,.1,.5],'z_extent_um':8,'cuboid_voxels':cube['voxel_count'],'exact_sum_check':True,'timings':timings,'process_peak_rss_bytes':int(rss if sys.platform=='darwin' else rss*1024),'scope':'One deterministic synthetic stack, local source service. Checks import, volume preparation, exact full-resolution cuboid sum, threshold mask and full-plane QC. Not a real acquisition, sustained batch stress test, native Windows result or quality validation.'}
Path('docs/LARGE_STACK_BENCHMARK.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
