import io,json,time
import numpy as np
import pytest,tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.segmentation import SegmentationRequest,segment_volume
from organelle_scope.experiments import ExperimentRequest,analyze_experiment,bh_adjust,normal_posterior
from organelle_scope.image_io import ImageError

def test_segmentation_known_objects_xyz_and_edits():
    a=np.zeros((5,8,9));a[1:3,2:4,3:6]=20;a[4,7,8]=30
    options=SegmentationRequest(x0=10,x1=18,y0=20,y1=27,z0=30,z1=34,method='manual',threshold=10,min_voxels=2)
    labels,r=segment_volume(a,options,[.5,.2,.1]);assert r['object_count']==1 and r['foreground_voxels']==12
    o=r['objects'][0];assert o['volume_um3']==pytest.approx(.12)
    np.testing.assert_allclose(o['centroid_zyx'],[31.5,22.5,14]);assert not o['touches_cuboid_edge']
    assert r['mesh']['units']=='um';assert max(v[0] for v in r['mesh']['vertices_xyz'])<=1.55
    options.exclude_labels=[o['label']];assert segment_volume(a,options,[.5,.2,.1])[1]['object_count']==0
    assert segment_volume(np.ones((2,3,4)),SegmentationRequest(x0=0,x1=3,y0=0,y1=2,z0=0,z1=1),[None]*3)[1]['foreground_voxels']==0

def batch():
    items=[]
    for condition in ['control','treated']:
        for exp in range(3):
            for cell in range(2):
                values=[10+exp+cell+20*(condition=='treated')]*2
                rows=[{'roi':{'id':str(i)},'channel_summary':[{'channel':0,'mean':v}],'pairs':[]} for i,v in enumerate(values)]
                items.append({'condition':condition,'experiment':str(exp),'cell':str(cell),'status':'completed','image_id':str(len(items)),'result':{'request':{'threshold_mode':'zero'},'processing':{},'source_sha256':'hash','results':rows}})
    return {'id':'batch','items':items}

def test_experiment_units_pairing_posterior_and_bh():
    run=batch();o=ExperimentRequest(run_id='x',conditions=['control','treated'],design='paired_experiments',metric='mean',iterations=199,normal_model=True)
    a=analyze_experiment(run,o);b=analyze_experiment(run,o);assert a==b
    assert a['groups'][0]['independent_experiments']==3 and a['groups'][0]['cells']==6
    assert a['groups'][0]['mean']==11.5;assert a['contrasts'][0]['difference_b_minus_a']==20
    assert a['contrasts'][0]['permutation_p_two_sided']==.25
    np.testing.assert_allclose(bh_adjust([.01,.04,.03]),[.03,.04,.04])
    posterior=normal_posterior([10,11,12],o);assert posterior['credible_interval_95'][0]<posterior['posterior_mean']<posterior['credible_interval_95'][1]
    o.design='independent_experiments'
    with pytest.raises(ImageError,match='distinct experiment'):analyze_experiment(run,o)
    run['items'][0]['experiment']=''
    with pytest.raises(ImageError,match='experiment ID'):analyze_experiment(run,o)

def test_segmentation_api_containment_proximity_export(tmp_path):
    a=np.zeros((2,3,10,10),np.uint16);a[0,1,3:5,3:5]=100;a[1,1,3:5,5:7]=200
    buf=io.BytesIO();tifffile.imwrite(buf,a,ome=True,photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':.5})
    with TestClient(create_app(tmp_path,'test')) as c:
        h={'X-Session-Token':'test'};im=c.post('/api/images',headers=h,files={'file':('s.tif',buf.getvalue())}).json();base='/api/images/'+im['id'];body={'x0':2,'x1':7,'y0':2,'y1':6,'z0':0,'z1':2,'method':'manual','threshold':10,'min_voxels':1,'reference_channel':1,'reference_threshold':10,'near_distance_um':.1}
        r=c.post(base+'/segmentation',headers=h,json=body);assert r.status_code==200,r.text
        result=r.json();assert result['foreground_voxels']==4 and result['objects'][0]['channel_intensities'][0]['sum']==400
        assert result['proximity']['fraction_marker_voxels_within_distance']==.5
        assert c.post(base+'/segmentation/export',headers=h,json=body).status_code==200
        assert c.post(base+'/segmentation',headers=h,json={**body,'x1':99}).status_code==422

def test_radial_shells_are_clipped_to_cuboid_and_empty_bins_undefined(tmp_path):
    a=np.ones((3,5,5),np.uint16)*10;a[1,2,2]=100
    buf=io.BytesIO();tifffile.imwrite(buf,a,ome=True,photometric='minisblack',metadata={'axes':'ZYX','PhysicalSizeX':1,'PhysicalSizeY':1,'PhysicalSizeZ':1})
    with TestClient(create_app(tmp_path,'test')) as c:
        h={'X-Session-Token':'test'};im=c.post('/api/images',headers=h,files={'file':('r.tif',buf.getvalue())}).json()
        body={'x0':0,'x1':4,'y0':0,'y1':4,'z0':0,'z1':2,'method':'manual','threshold':50,'min_voxels':1,'radial_bin_um':1,'radial_max_um':6}
        report=c.post('/api/images/'+im['id']+'/segmentation',headers=h,json=body).json();radial=report['radial_enrichment'];assert radial['center_source_zyx']==[1,2,2]
        shells=radial['channels'][0]['shells'];assert sum(s['voxel_count'] for s in shells)==75
        assert shells[0]['mean']==100 and shells[-1]['mean'] is None
        assert shells[0]['enrichment_over_cuboid_mean']==pytest.approx(100/a.mean())


def test_normal_inverse_gamma_posterior_matches_analytic_parameters():
    o=ExperimentRequest(run_id='x',conditions=['a','b'],design='independent_experiments',prior_mean=0,prior_kappa=1,prior_alpha=2,prior_beta=1)
    p=normal_posterior([1,2,3],o)
    assert p['posterior_mean']==1.5 and p['student_t_df']==7 and p['student_t_scale']==.5
    assert p['posterior_expected_sigma_squared']==1.4 and p['posterior_variance_mu']==.35

def test_completed_real_batch_flows_into_experiment_api(tmp_path):
    with TestClient(create_app(tmp_path,'test')) as c:
        h={'X-Session-Token':'test'};items=[]
        for condition,offset in [('control',0),('treated',100)]:
            for experiment in range(3):
                a=np.arange(2*12*12,dtype=np.uint16).reshape(2,12,12)+offset+experiment*10;b=io.BytesIO();tifffile.imwrite(b,a,ome=True,photometric='minisblack',metadata={'axes':'CYX'})
                im=c.post('/api/images',headers=h,files={'file':('experiment.tif',b.getvalue())}).json()
                items.append({'image_id':im['id'],'reviewed':True,'condition':condition,'experiment':condition+str(experiment),'cell':'cell','analysis':{'threshold_mode':'zero','rois':[{'id':'r','kind':'polygon','z':0,'points':[{'x':1,'y':1},{'x':10,'y':1},{'x':10,'y':10},{'x':1,'y':10}]}]}})
        session=c.post('/api/batch/sessions',headers=h,json={'name':'Inference integration','items':items});assert session.status_code==200,session.text
        s=session.json();job=c.post('/api/batch/runs',headers=h,json={'session_id':s['id'],'revision':s['revision']}).json()
        for _ in range(200):
            run=c.get('/api/batch/runs/'+job['id'],headers=h).json()
            if run['status']!='running':break
            time.sleep(.01)
        assert run['status']=='completed',run
        report=c.post('/api/experiments/analyze',headers=h,json={'run_id':run['id'],'conditions':['control','treated'],'design':'independent_experiments','metric':'mean','iterations':199});assert report.status_code==200,report.text
        assert report.json()['contrasts'][0]['difference_b_minus_a']==100
        assert report.json()['contrasts'][0]['minimum_attainable_two_sided_p']==.1
        assert c.post('/api/experiments/analyze',json={}).status_code==401
