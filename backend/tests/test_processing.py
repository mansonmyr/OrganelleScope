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


@pytest.mark.parametrize('dtype,height',[(np.uint8,None),(np.uint16,1500.)])
def test_rolling_ball_matches_explicit_spherical_surface_reference(dtype,height):
    # Independent scalar geometry calculation, including edges and >8-bit values.
    import math
    raw=np.random.default_rng(17).integers(0,200 if dtype==np.uint8 else 60000,(6,7),dtype=dtype)
    original=raw.copy();radius=2;h=height if height is not None else radius
    expected=np.empty(raw.shape,np.float64)
    for y,x in np.ndindex(raw.shape):
        candidates=[]
        for yy,xx in np.ndindex(raw.shape):
            d=(yy-y)**2+(xx-x)**2
            if d<=radius**2:
                candidates.append(float(raw[yy,xx])+h*(1-math.sqrt(1-d/radius**2)))
        expected[y,x]=max(float(raw[y,x])-min(candidates),0)
    result=process_plane(raw,ProcessingConfig(background='rolling_ball',radius_px=radius,rolling_height=height),0)
    np.testing.assert_allclose(result,expected,atol=.005,rtol=1e-6)
    np.testing.assert_array_equal(raw,original)
    assert result.dtype==np.float32 and np.isfinite(result).all() and (result>=0).all()


def test_rolling_ball_constant_background_and_curvature_are_not_square_opening():
    radius=3
    raw=np.full((11,11),1000,np.uint16);raw[5,5]=1500
    ball=process_plane(raw,ProcessingConfig(background='rolling_ball',radius_px=radius),0)
    expected_peak=500-radius*(1-np.sqrt(1-1/radius**2))
    assert ball[5,5]==pytest.approx(expected_peak,abs=.0001)
    assert np.count_nonzero(ball)==1
    np.testing.assert_array_equal(process_plane(np.full((5,6),65535,np.uint16),ProcessingConfig(background='rolling_ball'),0),0)
    opening=process_plane(raw,ProcessingConfig(background='opening',radius_px=radius),0)
    assert opening[5,5]==500 and ball[5,5]!=opening[5,5]


@pytest.mark.parametrize('settings',[{'radius_px':101},{'rolling_height':0},{'rolling_height':float('nan')},{'rolling_height':65536}])
def test_rolling_ball_rejects_unsafe_or_invalid_kernel(settings):
    with pytest.raises(ValidationError):ProcessingConfig(background='rolling_ball',**settings)


def test_rolling_ball_plane_preview_and_recipe_api(tmp_path):
    raw=np.full((2,9,9),1000,np.uint16);raw[:,4,4]=60000
    stream=io.BytesIO();tifffile.imwrite(stream,raw,ome=True,photometric='minisblack',metadata={'axes':'CYX'})
    h={'X-Session-Token':'test'}
    recipe={'background':'rolling_ball','radius_px':2,'rolling_height':250}
    with TestClient(create_app(tmp_path,'test')) as client:
        record=client.post('/api/images',headers=h,files={'file':('ball.tif',stream.getvalue())}).json();url='/api/images/'+record['id']
        response=client.post(url+'/processing/plane?channel=0',headers=h,json=recipe)
        assert response.status_code==200,response.text
        np.testing.assert_array_equal(np.frombuffer(response.content,'<f4').reshape(9,9),process_plane(raw[0],ProcessingConfig(**recipe),0))
        assert client.post(url+'/processing/preview',headers=h,json=recipe).status_code==200
        report=client.post(url+'/processing/recipe',headers=h,json=recipe).json()
        assert report['rolling_ball']['height_native_intensity']==250
        assert report['rolling_ball']['radius_xy_px']==2
        changed=client.post(url+'/processing/recipe',headers=h,json={**recipe,'rolling_height':500}).json()
        assert report['recipe_sha256']!=changed['recipe_sha256']
        assert (tmp_path/record['id']/'source.tiff').read_bytes()==stream.getvalue()
