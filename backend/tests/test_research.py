import io
import numpy as np
import pytest
import tifffile
from fastapi.testclient import TestClient
from PIL import Image
from organelle_scope.main import create_app
from organelle_scope.roi_analysis import AreaROI, roi_mask
from organelle_scope.spatial_validation import spatial_shift, reference_benchmarks


def test_translation_matches_exhaustive_independent_reference():
    rng=np.random.default_rng(19);a=rng.normal(size=(6,7));b=a.copy()
    roi=AreaROI(id='r',kind='polygon',z=0,points=[{'x':0,'y':0},{'x':6,'y':0},{'x':6,'y':5},{'x':0,'y':5}])
    result=spatial_shift(a,b,roi,99,1729)
    expected=[np.corrcoef(a.ravel(),np.roll(b,(-dy,-dx),(0,1)).ravel())[0,1] for dy in range(6) for dx in range(7) if (dy,dx)!=(0,0)]
    np.testing.assert_allclose(result['null_scores'],expected,atol=1e-12)
    assert result['exhaustive'] and result['iterations']==41
    assert result['tail_probability']==pytest.approx(1/42)
    assert reference_benchmarks()['passed']


def test_monte_carlo_reproducible_and_constant_rejected():
    rng=np.random.default_rng(19);a=rng.normal(size=(12,13));b=rng.normal(size=a.shape)
    roi=AreaROI(id='r',kind='circle',z=0,points=[{'x':6,'y':6},{'x':9,'y':6}])
    first=spatial_shift(a,b,roi,25,31);second=spatial_shift(a,b,roi,25,31)
    assert first==second and not first['exhaustive']
    assert first['null_scores']!=spatial_shift(a,b,roi,25,32)['null_scores']
    with pytest.raises(ValueError,match='constant'):spatial_shift(a,np.ones_like(a),roi,25,31)


@pytest.fixture
def volume_client(tmp_path):
    data=np.arange(2*4*6*7,dtype=np.uint16).reshape(2,4,6,7)+100
    buf=io.BytesIO();tifffile.imwrite(buf,data,ome=True,photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.2,'PhysicalSizeZ':.5})
    with TestClient(create_app(tmp_path,'test')) as client:
        h={'X-Session-Token':'test'}
        record=client.post('/api/images',headers=h,files={'file':('v.tif',buf.getvalue())}).json()
        yield client,h,'/api/images/'+record['id'],data


def test_orthogonal_planes_preserve_source_orientation_and_auth(volume_client):
    client,h,url,data=volume_client
    assert client.get(url+'/orthogonal').status_code==401
    for axis,expected in [('XY',data[0,2]),('XZ',data[0,:,3,:]),('YZ',data[0,:,:,4])]:
        response=client.get(url+f'/orthogonal?axis={axis}&x=4&y=3&z=2&channel=0',headers=h)
        assert response.status_code==200,response.text
        pixels=np.asarray(Image.open(io.BytesIO(response.content)))
        high=np.percentile(data[0,2,::4,::4],99.5)
        expected_rgb=(np.clip(np.clip(expected/high,0,1)[...,None]*np.array([1,.12,.25]),0,1)*255).astype(np.uint8)
        np.testing.assert_array_equal(pixels,expected_rgb)
    assert client.get(url+'/orthogonal?axis=ZX',headers=h).status_code==422
    assert client.get(url+'/orthogonal?x=99',headers=h).status_code==422


def test_full_resolution_cuboid_sums_volumes_and_recipe(volume_client):
    client,h,url,data=volume_client
    bounds={'x0':1,'x1':3,'y0':2,'y1':4,'z0':1,'z1':3}
    assert client.post(url+'/cuboid',json=bounds).status_code==401
    result=client.post(url+'/cuboid',headers=h,json=bounds)
    assert result.status_code==200,result.text
    result=result.json();assert result['voxel_count']==27
    assert result['region_volume_um3']==pytest.approx(27*.1*.2*.5)
    assert result['channels'][0]['sum']==int(data[0,1:4,2:5,1:4].sum())
    assert result['pairs'][0]['pcc']==pytest.approx(1)
    processed=client.post(url+'/cuboid',headers=h,json={**bounds,'processing':{'background':'constant','offsets':[100,100]}}).json()
    assert processed['channels'][0]['sum']==result['channels'][0]['sum']-2700
    assert processed['source_sha256']==result['source_sha256']
    assert client.post(url+'/cuboid',headers=h,json={**bounds,'x1':99}).status_code==422
    assert client.post(url+'/cuboid',headers=h,json={**bounds,'z0':3,'z1':1}).status_code==422


def test_sensitivity_uses_matching_thresholds_and_spatial_requires_model_choice(volume_client):
    client,h,url,data=volume_client
    roi={'id':'r','kind':'circle','z':1,'points':[{'x':3,'y':3},{'x':5,'y':3}]}
    config={'background':'constant','offsets':[100,100]}
    request={'rois':[roi],'processing':config,'threshold_mode':'zero'}
    report=client.post(url+'/validation/sensitivity',headers=h,json=request)
    assert report.status_code==200,report.text
    result=report.json()['results'][0]
    mask,_=roi_mask(AreaROI(**roi),(6,7))
    assert result['processed']['channel_summary'][0]['sum']==float(data[0,1][mask].sum())-100*mask.sum()
    assert result['deltas_processed_minus_raw'][0]['pcc']==pytest.approx(0,abs=1e-12)
    assert client.post(url+'/validation/sensitivity',headers=h,json={**request,'threshold_mode':'costes'}).status_code==422
    test={'roi':roi,'iterations':25,'seed':14}
    assert client.post(url+'/validation/spatial',headers=h,json=test).status_code==422
    spatial=client.post(url+'/validation/spatial',headers=h,json={**test,'acknowledge_stationarity':True})
    assert spatial.status_code==200,spatial.text
    assert spatial.json()['iterations']==25
    assert 'source_sha256' in spatial.json()
    assert client.get('/api/validation/reference',headers=h).json()['passed']


def test_cuboid_rgb_decoder_and_all_pair_values_match_independent_array_reference(tmp_path):
    from scipy.stats import spearmanr
    rng=np.random.default_rng(52)
    data=np.zeros((4,11,13,3),dtype=np.uint8)
    data[...,0]=rng.integers(0,80,data.shape[:-1]);data[...,1]=rng.integers(0,70,data.shape[:-1])
    stream=io.BytesIO();tifffile.imwrite(stream,data,photometric='rgb',metadata={'axes':'ZYXS'})
    with TestClient(create_app(tmp_path,'test')) as client:
        h={'X-Session-Token':'test'}
        image=client.post('/api/images',headers=h,files={'file':('rgb.tif',stream.getvalue())}).json()
        url='/api/images/'+image['id']
        image=client.post(url+'/inspect',headers=h,json={'axes':'ZYXC','spacing_um':{'X':.1,'Y':.2,'Z':.4}}).json()
        bounds={'x0':2,'x1':8,'y0':1,'y1':7,'z0':1,'z1':3}
        response=client.post(url+'/cuboid',headers=h,json=bounds);assert response.status_code==200,response.text
        out=response.json();assert out['voxel_count']==147
        # Direct TIFF array read, independent of the application's plane reader/crop path.
        with tifffile.TiffFile(io.BytesIO(stream.getvalue())) as tf:direct=tf.series[0].asarray()[1:4,1:8,2:9]
        a,b=direct[...,0].astype(float).ravel(),direct[...,1].astype(float).ravel()
        pair=out['pairs'][0]
        assert pair['pcc']==pytest.approx(np.corrcoef(a,b)[0,1],abs=1e-12)
        assert pair['spearman']==pytest.approx(spearmanr(a,b).statistic,abs=1e-12)
        assert pair['m1']==pytest.approx(a[b>0].sum()/a.sum())
        assert pair['m2']==pytest.approx(b[a>0].sum()/b.sum())
        for i in range(3):
            assert out['channels'][i]['sum']==float(direct[...,i].sum())
            assert out['channels'][i]['std']==pytest.approx(direct[...,i].std())
        assert out['channels'][2]['above_threshold_voxels']==0
        assert out['pairs'][1]['pcc'] is None and out['pairs'][1]['m1']==0 and out['pairs'][1]['m2'] is None
        assert 'only zero' in out['pairs'][1]['unavailable_reasons']['pcc']
        assert any('RGB' in w for w in out['image_info']['warnings'])
