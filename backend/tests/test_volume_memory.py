"""Reduced volume slices must not retain full source planes until stacking."""
import io,weakref
import numpy as np
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app


def test_volume_releases_source_planes_and_preserves_pixels(tmp_path,monkeypatch):
    import organelle_scope.main as module
    h={'X-Session-Token':'test'};stream=io.BytesIO()
    tifffile.imwrite(stream,np.zeros((2,8,256,256),dtype='uint16'),ome=True,photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.2,'PhysicalSizeZ':.5})
    refs=[];live=[]
    def decode(path,info,channel,z):
        live.append(sum(ref() is not None for ref in refs))
        plane=np.full((256,256),z+100*channel,dtype='uint16');refs.append(weakref.ref(plane));return plane
    with TestClient(create_app(tmp_path/'images','test')) as client:
        image=client.post('/api/images',headers=h,files={'file':('stack.tif',stream.getvalue())}).json()
        monkeypatch.setattr(module,'read_plane',decode)
        response=client.get('/api/images/'+image['id']+'/volume?channel=1',headers=h)
        assert response.status_code==200,response.text
        values=np.frombuffer(response.content,'<u2').reshape((8,128,128))
        np.testing.assert_array_equal(values,np.stack([np.full((128,128),100+z,dtype='uint16') for z in range(8)]))
        assert max(live)<=1,'Downsampled views retained prior full source planes.'
        assert not any(ref() is not None for ref in refs)
