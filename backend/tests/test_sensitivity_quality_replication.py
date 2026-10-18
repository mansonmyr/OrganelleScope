import copy,io
import numpy as np
import pytest
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.experiments import ExperimentRequest,analyze_experiment
from organelle_scope.image_io import ImageError


def uploaded(client):
    a=np.zeros((2,3,11,11),np.uint16)
    a[0,1,3:8,3:8]=30;a[1,1,4:7,4:7]=50;a[0,1,5,5]=4095
    stream=io.BytesIO();tifffile.imwrite(stream,a,ome=True,photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.2,'PhysicalSizeY':.2,'PhysicalSizeZ':1})
    record=client.post('/api/images',headers={'X-Session-Token':'t'},files={'file':('sweep.tif',stream.getvalue())}).json()
    return record,a


def test_roi_size_threshold_sweep_matches_direct_pixel_oracle_and_preserves_source(tmp_path):
    with TestClient(create_app(tmp_path,'t')) as client:
        image,a=uploaded(client);url='/api/images/'+image['id'];h={'X-Session-Token':'t'}
        roi={'id':'r','kind':'circle','z':1,'points':[{'x':5,'y':5},{'x':7,'y':5}]}
        body={'rois':[roi],'threshold_mode':'manual','thresholds':[10,10],'threshold_step':20,'size_fraction':.2}
        response=client.post(url+'/validation/parameter-sweep',headers=h,json=body);assert response.status_code==200,response.text
        variants={v['variant']:v for v in response.json()['results'][0]['variants']}
        assert [variants[k]['result']['pixel_count'] for k in ['size_smaller','baseline','size_larger']]==[9,13,21]
        yy,xx=np.indices((11,11));mask=(xx-5)**2+(yy-5)**2<=4
        av,bv=a[0,1][mask],a[1,1][mask]
        expected=float(av[bv>30].sum(dtype=float)/av.sum(dtype=float))
        assert variants['threshold_C2_higher']['result']['pairs'][0]['thresholded_m1']==pytest.approx(expected)
        assert variants['threshold_C1_lower']['thresholds']==[0,10]
        assert client.get(url,headers=h).json()['sha256']==image['sha256']
        assert client.post(url+'/validation/parameter-sweep',headers=h,json={**body,'threshold_mode':'costes'}).status_code==422


def test_volume_sensitivity_has_explicit_baseline_bounds_and_empty_reference(tmp_path):
    with TestClient(create_app(tmp_path,'t')) as client:
        image,_=uploaded(client);h={'X-Session-Token':'t'};url='/api/images/'+image['id']
        body={'x0':2,'x1':8,'y0':2,'y1':8,'z0':0,'z1':2,'method':'manual','threshold':20,'min_voxels':1,'reference_channel':1,'reference_threshold':40,'threshold_step':20,'boundary_step':1}
        response=client.post(url+'/segmentation/sensitivity',headers=h,json=body);assert response.status_code==200,response.text
        rows={r['variant']:r for r in response.json()['variants']}
        assert len(rows)==7
        assert rows['baseline']['foreground_voxels']==25
        assert rows['cuboid_smaller']['request']['z0']==rows['cuboid_smaller']['request']['z1']==1
        assert rows['reference_threshold_higher']['proximity']['unavailable_reason']=='Reference mask is empty.'
        assert client.post(url+'/segmentation/sensitivity',headers=h,json={**body,'method':'otsu'}).status_code==422


def test_quality_separates_declared_ceiling_sampling_and_unknown_registration(tmp_path):
    with TestClient(create_app(tmp_path,'t')) as client:
        image,_=uploaded(client);h={'X-Session-Token':'t'};url='/api/images/'+image['id']+'/quality?z=1'
        original=client.get(url,headers=h).json()
        assert original['channels'][0]['storage_ceiling_pixels']==0
        assert original['channels'][0]['at_or_above_declared_ceiling_pixels'] is None
        supplied=client.get(url+'&detector_ceiling=4095&lateral_resolution_um=0.5&axial_resolution_um=0.6',headers=h).json()
        assert supplied['channels'][0]['at_or_above_declared_ceiling_pixels']==1
        assert supplied['channels'][0]['detector_saturation']=='not determined'
        assert supplied['sampling_review']['axes'][0]['samples_per_declared_resolution']==2.5
        assert 'Coarser' in supplied['sampling_review']['axes'][2]['status']
        assert 'Not measured' in supplied['sampling_review']['registration']
        assert client.get(url+'&lateral_resolution_um=nan',headers=h).status_code==422
        assert client.get(url+'&detector_ceiling=100000',headers=h).status_code==422


def experiment_fixture():
    items=[]
    for condition,offset in [('control',0),('treated',100)]:
        for experiment in range(3):
            for cell in range(2):
                digest=f'{condition}-{experiment}-{cell}'
                roi={'id':'r','kind':'polygon','z':0,'points':[{'x':0,'y':0},{'x':1,'y':0},{'x':1,'y':1}]}
                items.append({'image_id':digest,'image':{'sha256':digest},'status':'completed','condition':condition,'experiment':condition+str(experiment),'cell':str(cell),'result':{'source_sha256':digest,'image_info':{'channel_labels':['Marker']},'request':{'threshold_mode':'zero'},'processing':{},'results':[{'roi':roi,'channel_summary':[{'channel':0,'mean':offset+experiment+cell}],'pairs':[]}]}})
    return {'id':'test','items':items}


def test_more_roi_values_do_not_inflate_experiment_count_or_experiment_weight():
    run=experiment_fixture();options=ExperimentRequest(run_id='test',conditions=['control','treated'],design='independent_experiments',metric='mean',iterations=199)
    baseline=analyze_experiment(run,options)
    row=run['items'][0]['result']['results'][0]
    for i in range(1,20):
        new=copy.deepcopy(row);new['roi']['id']=str(i);new['roi']['points'][0]['x']=i+1;run['items'][0]['result']['results'].append(new)
    result=analyze_experiment(run,options)
    assert result['groups'][0]['independent_experiments']==3
    assert result['groups'][0]['cells']==6
    assert result['contrasts'][0]['difference_b_minus_a']==baseline['contrasts'][0]['difference_b_minus_a']==100
    assert result['replication_review']['conditions'][0]['roi_values']==25
    assert result['replication_review']['independence_verified'] is False


def test_renaming_a_repeated_region_does_not_create_a_new_cell():
    run=experiment_fixture();duplicate=copy.deepcopy(run['items'][0]);duplicate['image_id']='copy';duplicate['cell']='renamed';duplicate['result']['results'][0]['roi']['id']='renamed';run['items'].append(duplicate)
    with pytest.raises(ImageError,match='same raw-source ROI geometry'):
        analyze_experiment(run,ExperimentRequest(run_id='test',conditions=['control','treated'],design='independent_experiments',metric='mean',iterations=199))


def test_polygon_order_and_circle_edge_direction_do_not_create_new_geometry():
    from organelle_scope.batch_design import roi_geometry_key
    polygon={'kind':'polygon','z':0,'points':[{'x':0,'y':0},{'x':1,'y':0},{'x':1,'y':1}]}
    reversed_polygon={**polygon,'points':list(reversed(polygon['points']))}
    assert roi_geometry_key(polygon,{})==roi_geometry_key(reversed_polygon,{})
    circle={'kind':'circle','z':0,'points':[{'x':5,'y':5},{'x':7,'y':5}]}
    other={**circle,'points':[{'x':5,'y':5},{'x':5,'y':3}]}
    assert roi_geometry_key(circle,{})==roi_geometry_key(other,{})
