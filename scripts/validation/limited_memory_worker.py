"""Linux-only hard virtual-address-space budget; not a whole-machine RAM emulator."""
import argparse,io,json,platform,resource,tempfile
from pathlib import Path
import numpy as np
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--address-limit-mib',type=int,default=1536);args=p.parse_args()
    if platform.system()!='Linux':raise SystemExit('RLIMIT_AS qualification is supported only on Linux.')
    limit=args.address_limit_mib*1024**2
    resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
    headers={'X-Session-Token':'limited-memory'}
    with tempfile.TemporaryDirectory(prefix='OrganelleScope-limited-') as directory:
        folder=Path(directory);path=folder/'source.tif';base=np.arange(2048,dtype='uint16')[None,:]+np.zeros((2048,1),dtype='uint16')
        tifffile.imwrite(path,(base+c*100+z for c in range(4) for z in range(8)),shape=(4,8,2048,2048),dtype='uint16',ome=True,photometric='minisblack',compression='deflate',maxworkers=1,metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':.4})
        with TestClient(create_app(folder/'profile/images','limited-memory')) as client:
            with path.open('rb') as stream:response=client.post('/api/images',headers=headers,files={'file':('synthetic.tif',stream)});response.raise_for_status();image=response.json()
            response=client.get('/api/images/'+image['id']+'/volume?units=voxel',headers=headers);response.raise_for_status()
            volume=np.frombuffer(response.content,'<u2').reshape((8,128,128))
            np.testing.assert_array_equal(volume,np.stack([(base+z)[::16,::16] for z in range(8)]))
            options={'rois':[{'id':'center','kind':'circle','z':4,'points':[{'x':1024,'y':1024},{'x':1032,'y':1024}]}],'threshold_mode':'zero'}
            response=client.post('/api/images/'+image['id']+'/analysis',headers=headers,json=options);response.raise_for_status();row=response.json()['results'][0]
            yy,xx=np.mgrid[1016:1033,1016:1033];mask=(xx-1024)**2+(yy-1024)**2<=64
            assert row['pixel_count']==int(mask.sum())
            for c in range(4):assert row['channel_summary'][c]['sum']==int((base[1016:1033,1016:1033]+c*100+4)[mask].sum(dtype='uint64'))
        print(json.dumps({'status':'passed','platform':'Linux','hard_address_space_limit_bytes':limit,'decoded_stack_bytes':4*8*2048**2*2,'volume_and_roi_exact':True,'scope':'Source service in an isolated worker under RLIMIT_AS, without Gemma/GPU. This is not testing an entire low-RAM computer or native Mac/Windows installation.'}))
if __name__=='__main__':main()
