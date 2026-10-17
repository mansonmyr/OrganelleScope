import io

import numpy as np
import pytest
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.image_io import ImageError
from organelle_scope.main import create_app
from organelle_scope.roi_analysis import AreaROI, roi_mask, pair_metrics, regression, automatic_thresholds, pearson


def region(kind='polygon', points=None, z=0):
    return AreaROI(id='region', kind=kind, z=z, points=points or [{'x':0,'y':0},{'x':3,'y':0},{'x':3,'y':3},{'x':0,'y':3}])


def test_polygon_and_circle_include_boundary_pixel_centers():
    mask,_ = roi_mask(region(),(5,5))
    assert mask.sum()==16 and mask[3,3] and not mask[4,3]
    circle=region('circle',[{'x':2,'y':2},{'x':3,'y':2}])
    mask,_=roi_mask(circle,(5,5))
    assert mask.sum()==5
    assert mask[2,1] and not mask[1,1]


def test_invalid_polygon_and_small_circle_rejected():
    with pytest.raises(ImageError, match='Self-intersecting'):
        roi_mask(region(points=[{'x':0,'y':0},{'x':3,'y':3},{'x':3,'y':0},{'x':0,'y':3}]),(5,5))
    with pytest.raises(ImageError, match='three pixel'):
        roi_mask(region('circle',[{'x':2,'y':2},{'x':2.1,'y':2}]),(5,5))


def test_known_coefficients_manders_denominators_and_undefined():
    a=np.array([0,1,2,3]);b=np.array([0,2,4,6])
    result=pair_metrics(a,b,'manual',1,4)
    assert result['pcc']==pytest.approx(1)
    assert result['spearman']==pytest.approx(1)
    assert result['moc']==pytest.approx(1)
    assert result['m1']==1 and result['m2']==1
    assert result['thresholded_m1']==pytest.approx(3/6)
    assert result['thresholded_m2']==pytest.approx(10/12)
    zero=pair_metrics(np.zeros(4),b,'costes')
    assert zero['pcc'] is None and zero['moc'] is None and zero['m1'] is None
    assert zero['thresholded_m1'] is None
    assert pair_metrics(a,a[::-1],'zero')['pcc']==pytest.approx(-1)


def test_automatic_threshold_search_matches_direct_pixel_search():
    rng=np.random.default_rng(17)
    for _ in range(25):
        a=rng.integers(0,25,80).astype(float)
        b=np.clip(a*.7+rng.normal(0,8,80),0,30).astype(int).astype(float)
        x=a-a.mean();y=b-b.mean();va=x@x;vb=y@y;cov=x@y
        slope=(vb-va+np.sqrt((vb-va)**2+4*cov**2))/(2*cov)
        intercept=b.mean()-slope*a.mean()
        swapped=slope>1
        main,other=(b,a) if swapped else (a,b)
        m,offset=(1/slope,-intercept/slope) if swapped else (slope,intercept)
        expected=None
        for t in range(int(main.max()),-1,-1):
            subset=(main<=t)|(other<=m*t+offset)
            r=pearson(main[subset],other[subset]) if subset.sum()>=3 else None
            if r is not None and r<=0 and m*t+offset>=0:
                expected=t;break
        actual=automatic_thresholds(a,b)
        if expected is None: assert actual['status']=='not_found'
        else: assert actual['b' if swapped else 'a']==expected


def test_regression_signed_and_collinear_coefficients():
    a=np.arange(10,dtype=float);b=a[::-1].copy()
    fit=regression([a,b],0,['A','B'])
    assert fit['r_squared']==pytest.approx(1)
    assert fit['betas'][0]['value']==pytest.approx(-1)
    unidentifiable=regression([a,b,b*2],0,['A','B','C'])
    assert all(x['value'] is None for x in unidentifiable['betas'])
    assert unidentifiable['coefficient_ratio'] is None


def test_roi_api_native_z_plane_persistence_and_validation(tmp_path):
    source=np.zeros((3,2,5,5),dtype=np.uint16)
    source[0,1]=np.arange(25).reshape(5,5)*100
    source[1,1]=source[0,1]*2
    source[2,1]=source[0,1]*3
    buf=io.BytesIO();tifffile.imwrite(buf,source,ome=True,photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.2})
    h={'X-Session-Token':'test'}
    with TestClient(create_app(tmp_path,'test')) as client:
        iid=client.post('/api/images',headers=h,files={'file':('test.ome.tiff',buf.getvalue())}).json()['id']
        url=f'/api/images/{iid}/analysis'
        req={'rois':[region(z=1).model_dump()],'threshold_mode':'zero'}
        assert client.post(url,json=req).status_code==401
        response=client.post(url,headers=h,json=req)
        assert response.status_code==200,response.text
        result=response.json()['results'][0]
        assert result['pixel_count']==16
        assert result['area_um2']==pytest.approx(.32)
        assert len(result['pairs'])==3
        assert result['pairs'][0]['pcc']==pytest.approx(1)
        assert result['channel_summary'][0]['mean']==pytest.approx(source[0,1,:4,:4].mean())
        req['threshold_mode']='manual';req['thresholds']=[-1,0,0]
        assert client.post(url,headers=h,json=req).status_code==422
        req['threshold_mode']='zero';req['rois'][0]['z']=9
        assert client.post(url,headers=h,json=req).status_code==422
    with TestClient(create_app(tmp_path,'test')) as client:
        assert client.get(url,headers=h).json()==response.json()
        client.post(f'/api/images/{iid}/inspect',headers=h,json={'spacing_um':{'X':.3}})
        assert client.get(url,headers=h).status_code==409


def test_correlations_match_independent_scipy_reference_across_intensity_ranges():
    from scipy.stats import pearsonr, spearmanr
    rng=np.random.default_rng(29841)
    for maximum in (255,65535):
        for relation in ('independent','positive','negative','ties'):
            a=rng.integers(0,maximum+1,4096,dtype=np.uint16).astype(float)
            if relation=='independent': b=rng.integers(0,maximum+1,4096).astype(float)
            elif relation=='positive': b=np.clip(.8*a+rng.normal(0,maximum*.1,len(a)),0,maximum)
            elif relation=='negative': b=maximum-a
            else: a=np.floor(a/(maximum/10));b=np.floor(a/2)
            measured=pair_metrics(a,b,'manual',maximum*.2,maximum*.3)
            assert measured['pcc']==pytest.approx(pearsonr(a,b).statistic,abs=1e-12)
            assert measured['spearman']==pytest.approx(spearmanr(a,b).statistic,abs=1e-12)


def test_multichannel_regression_recovers_known_standardized_coefficients():
    # Orthogonal predictors with known contributions, independent of least-squares implementation.
    a=np.array([-1,-1,1,1,-1,-1,1,1],dtype=float)
    b=np.array([-1,1,-1,1,-1,1,-1,1],dtype=float)
    y=3*a-2*b+20
    measured=regression([y,a+5,b+5],0,['Target','A','B'])
    assert measured['r_squared']==pytest.approx(1,abs=1e-12)
    assert measured['betas'][0]['value']==pytest.approx(3/np.sqrt(13),abs=1e-12)
    assert measured['betas'][1]['value']==pytest.approx(-2/np.sqrt(13),abs=1e-12)
    assert measured['coefficient_ratio']==pytest.approx(1.5,abs=1e-12)


def test_zero_channel_explains_each_undefined_metric_without_replacing_with_zero():
 a=np.arange(1,13,dtype=float);b=np.zeros(12)
 pair=pair_metrics(a,b,'zero')
 assert pair['pcc'] is None and pair['spearman'] is None and pair['moc'] is None
 assert pair['m1']==0 and pair['m2'] is None
 assert 'only zero' in pair['unavailable_reasons']['pcc']
 assert 'zero denominator' in pair['unavailable_reasons']['m2']
 assert 'm1' not in pair['unavailable_reasons']
