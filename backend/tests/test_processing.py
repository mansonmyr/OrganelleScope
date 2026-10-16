import io
import hashlib
import numpy as np
import pytest
import tifffile
from fastapi.testclient import TestClient
from pydantic import ValidationError
from organelle_scope.main import create_app
from organelle_scope.processing import ProcessingConfig, process_plane


def test_offset_subtraction_does_not_wrap_or_modify_source():
    raw=np.array([[0, 10, 65535],[20, 100, 500]],np.uint16);original=raw.copy()
    result=process_plane(raw,ProcessingConfig(background="constant",offsets=[20.5]),0)
    np.testing.assert_array_equal(raw,original)
    np.testing.assert_array_equal(result,[[0,0,65514.5],[0,79.5,479.5]])
    assert result.dtype==np.float32


def test_opening_recovers_known_isolated_signal_on_constant_background():
    raw=np.full((21,21),100,np.uint16);raw[10,10]=600
    result=process_plane(raw,ProcessingConfig(background="opening",radius_px=3),0)
    expected=np.zeros_like(raw);expected[10,10]=500
    np.testing.assert_array_equal(result,expected)


def test_gaussian_preserves_dc_and_impulse_flux_and_is_symmetric():
    config=ProcessingConfig(sigma_px=1.2)
    np.testing.assert_allclose(process_plane(np.full((41,41),123,np.uint16),config,0),123)
    impulse=np.zeros((41,41),np.uint16);impulse[20,20]=1000
    output=process_plane(impulse,config,0)
    assert output.sum()==pytest.approx(1000,rel=1e-6)
    np.testing.assert_array_equal(output,output[::-1,:]);np.testing.assert_array_equal(output,output[:,::-1])
    assert 0<output[20,20]<1000


@pytest.mark.parametrize('settings',[{'sigma_px':float('nan')},{'sigma_px':6},{'radius_px':0},{'radius_px':2.5},{'offsets':[float('inf')]},{'background':'rollingball'},{'surprise':True}])
def test_invalid_recipes_rejected(settings):
    with pytest.raises(ValidationError):ProcessingConfig(**settings)


def test_processing_api_records_recipe_and_preserves_raw_measurements(tmp_path):
    raw=np.full((2,9,9),100,np.uint16);raw[0,4,4]=600;raw[1,4,4]=1100
    stream=io.BytesIO();tifffile.imwrite(stream,raw,ome=True,photometric='minisblack',metadata={'axes':'CYX'})
    h={'X-Session-Token':'test'};recipe={'background':'constant','offsets':[100,100],'sigma_px':0}
    with TestClient(create_app(tmp_path,'test')) as client:
        record=client.post('/api/images',headers=h,files={'file':('signal.tif',stream.getvalue())}).json();url='/api/images/'+record['id']
        assert client.post(url+'/processing/plane',json=recipe).status_code==401
        response=client.post(url+'/processing/plane?channel=0',headers=h,json=recipe)
        data=np.frombuffer(response.content,'<f4').reshape(9,9)
        assert data[4,4]==500 and data.sum()==500
        assert client.post(url+'/processing/plane',headers=h,json={'background':'constant','offsets':[100]}).status_code==422
        assert client.post(url+'/processing/plane?channel=99',headers=h,json=recipe).status_code==422
        preview=client.post(url+'/processing/preview',headers=h,json=recipe)
        from PIL import Image
        comparison=Image.open(io.BytesIO(preview.content))
        assert comparison.size==(18,9)
        assert sum(comparison.getpixel((0,0)))>0
        assert comparison.getpixel((9,0))==(0,0,0)
        exported=client.post(url+'/processing/recipe',headers=h,json=recipe).json()
        assert exported['source_sha256']==record['sha256']
        changed=client.post(url+'/processing/recipe',headers=h,json={**recipe,'sigma_px':1}).json()
        assert changed['recipe_sha256']!=exported['recipe_sha256']
        body={'rois':[{'id':'r','kind':'circle','z':0,'points':[{'x':4,'y':4},{'x':6,'y':4}]}],'threshold_mode':'zero','processing':recipe}
        result=client.post(url+'/analysis',headers=h,json=body)
        assert result.status_code==200,result.text
        result=result.json();assert result['results'][0]['channel_summary'][0]['sum']==500
        assert result['processing']['settings']['offsets']==[100,100]
        assert result['processing']['dtype']=='float32'
        assert len(result['processing']['recipe_sha256'])==64
        assert result['processing']['recipe_sha256']==exported['recipe_sha256']
        assert client.get(url+'/analysis',headers=h).json()==result
        assert result['source_sha256']==hashlib.sha256(stream.getvalue()).hexdigest()
        body['threshold_mode']='costes'
        assert client.post(url+'/analysis',headers=h,json=body).status_code==422
        raw_response=client.get(url+'/plane',headers=h)
        np.testing.assert_array_equal(np.frombuffer(raw_response.content,'<u2').reshape(9,9),raw[0])
        body.pop('processing');body['threshold_mode']='zero'
        raw_result=client.post(url+'/analysis',headers=h,json=body).json()
        assert raw_result['results'][0]['channel_summary'][0]['sum']==500+13*100
        assert (tmp_path/record['id']/'source.tiff').read_bytes()==stream.getvalue()
