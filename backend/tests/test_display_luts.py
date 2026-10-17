import io
import numpy as np
import pytest
import tifffile
from PIL import Image
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.display_luts import display_colors
from organelle_scope.image_io import ImageError

def test_lut_validation_and_original_defaults():
    np.testing.assert_allclose(display_colors(None, 2), [[1,.12,.25],[.1,1,.65]])
    for bad in ('red', 'red,missing', 'red,blue,green', ''):
        with pytest.raises(ImageError): display_colors(bad,2)

def test_all_display_endpoints_change_colour_without_mutating_native_data(tmp_path):
    source=np.zeros((2,3,8,9),dtype=np.uint16);source[0,:,2:6,2:7]=100;source[1,:,1:3,1:3]=50
    buf=io.BytesIO();tifffile.imwrite(buf,source,ome=True,photometric='minisblack',metadata={'axes':'CZYX'})
    with TestClient(create_app(tmp_path,'token')) as c:
        headers={'X-Session-Token':'token'}
        record=c.post('/api/images',headers=headers,files={'file':('lut.tif',buf.getvalue())}).json();base='/api/images/'+record['id']
        analysis_request={'rois':[{'id':'roi','kind':'circle','z':1,'points':[{'x':4,'y':4},{'x':6,'y':4}]}],'target_channel':0,'threshold_mode':'zero','thresholds':[]}
        before=c.post(base+'/analysis',headers=headers,json=analysis_request).json()
        assert 'results' in before
        native=c.get(base+'/plane?channel=0&z=1',headers=headers).content
        recipe={'background':'constant','offsets':[10,5],'radius_px':20,'sigma_px':0}
        for path,post in [('/preview?z=1&contrast=auto',False),('/orthogonal?axis=XZ&y=4&z=1',False),('/processing/preview?z=1',True),('/processing/preview?z=1&view=background',True)]:
            def get(luts):
                return c.post(base+path+'&luts='+luts,headers=headers,json=recipe) if post else c.get(base+path+'&luts='+luts,headers=headers)
            red=get('red,red');blue=get('blue,blue');assert red.status_code==blue.status_code==200
            a=np.asarray(Image.open(io.BytesIO(red.content)));b=np.asarray(Image.open(io.BytesIO(blue.content)))
            assert a[...,0].max()>0 and a[...,1:].max()==0
            assert b[...,2].max()>0 and b[...,:2].max()==0
            np.testing.assert_array_equal(a[...,0],b[...,2])
            assert get('red,invalid').status_code==422
        assert c.get(base+'/plane?channel=0&z=1',headers=headers).content==native
        np.testing.assert_array_equal(np.frombuffer(native,'<u2').reshape(8,9),source[0,1])
        assert c.get(base,headers=headers).json()['sha256']==record['sha256']
        after=c.post(base+'/analysis',headers=headers,json=analysis_request).json()
        assert before['results']==after['results'] and before['request']==after['request']
