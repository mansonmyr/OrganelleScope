import io,json
import numpy as np
import pytest,tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.analysis_service import save_analysis
from organelle_scope.roi_analysis import AreaROI,analyze_roi,pair_metrics,automatic_thresholds
from organelle_scope.proximity import proximity_summary
from organelle_scope.experiments import ExperimentRequest,analyze_experiment


def test_roi_counts_raw_ceiling_per_region_after_processing_and_background_variation():
    raw=np.arange(36,dtype=np.uint16).reshape(6,6)+100
    raw[1:3,1:3]=65535
    bg=np.arange(36,dtype=np.float32).reshape(6,6)
    roi=AreaROI(id='r',kind='polygon',z=0,points=[{'x':1,'y':1},{'x':3,'y':1},{'x':3,'y':3},{'x':1,'y':3}])
    r=analyze_roi([raw.astype(float)-50,raw.astype(float)-50],roi,['A','B'],0,'manual',[0,0],(1,1),raw_channels=[raw,raw],backgrounds=[bg,bg],intensity_ceiling=65535)
    c=r['channel_summary'][0]
    assert r['pixel_count']==9 and c['raw_quality']['ceiling_samples']==4
    assert c['raw_quality']['ceiling_fraction']==pytest.approx(4/9)
    assert c['estimated_background']['min']==7 and c['estimated_background']['max']==21
    assert any('raw ROI samples' in w for w in r['warnings'])


def test_all_positive_thresholds_are_flagged_without_changing_coefficients():
    a=np.array([10,11,12,13]);b=np.array([20,22,24,26])
    r=pair_metrics(a,b,'manual',1,2)
    assert r['pcc']==pytest.approx(1) and r['thresholded_m1']==1
    assert r['threshold_occupancy']=={'samples':4,'above_a':4,'above_b':4,'all_above_a':True,'all_above_b':True}
    assert any('below every sample' in w for w in r['warnings'])
    assert not pair_metrics(a,b,'manual',11,22)['threshold_occupancy']['all_above_a']
    no=automatic_thresholds(a,np.zeros(4))
    assert no['algorithm']=='orthogonal-integer-union-1' and no['reason'] and no['background_samples']==0


def test_recalculation_archives_exact_old_report_and_history_is_authenticated(tmp_path):
    with TestClient(create_app(tmp_path,'test')) as c:
        h={'X-Session-Token':'test'};buf=io.BytesIO();data=np.arange(72,dtype=np.uint16).reshape(2,6,6)
        tifffile.imwrite(buf,data,ome=True,photometric='minisblack',metadata={'axes':'CYX'})
        image=c.post('/api/images',headers=h,files={'file':('test.tif',buf.getvalue())}).json();ident=image['id']
        options={'threshold_mode':'zero','rois':[{'id':'r','kind':'polygon','z':0,'points':[{'x':0,'y':0},{'x':5,'y':0},{'x':5,'y':5},{'x':0,'y':5}]}]}
        first=c.post(f'/api/images/{ident}/analysis',headers=h,json=options);assert first.status_code==200,first.text
        second=c.post(f'/api/images/{ident}/analysis',headers=h,json=options);assert second.status_code==200
        rows=c.get(f'/api/images/{ident}/analysis-history',headers=h).json();assert len(rows)==2
        preserved=[c.get(f'/api/images/{ident}/analysis-history/'+r['sha256'],headers=h).json() for r in rows]
        assert first.json() in preserved and second.json() in preserved
        assert first.json()['report_id']!=second.json()['report_id']
        assert c.get(f'/api/images/{ident}/analysis-history').status_code==401
        assert c.get(f'/api/images/{ident}/analysis-history/invalid',headers=h).status_code==404


def test_exact_legacy_report_bytes_survive_new_save(tmp_path):
    data=b'{"algorithm_version": "roi-3", "results": []}\n'
    (tmp_path/'analysis.json').write_bytes(data);save_analysis(tmp_path,{'algorithm_version':'roi-4-quality','results':[]})
    assert data in [p.read_bytes() for p in (tmp_path/'analysis-history').glob('*.json')]


def test_proximity_cutoff_and_containment_are_explained_without_changing_geometry():
    marker=np.zeros((4,5,5),bool);marker[1,2,2]=True;reference=np.ones_like(marker)
    r=proximity_summary(marker,reference,[.4,.065,.065],.25)
    assert r['marker_to_reference']['fraction_within_distance']==1
    assert r['sampling_review']['cutoff_smaller_than_z_step'] is True
    assert r['mask_occupancy']['reference_fraction']==1
    assert any('Containment' in w for w in r['quality_warnings'])
    assert any('cuboid face' in w for w in r['quality_warnings'])


def test_small_sample_defaults_are_estimation_only_and_show_sample_sd():
    items=[]
    for condition,offset in [('a',0),('b',5)]:
        for experiment in range(3):
            source=condition+str(experiment)
            result={'request':{'threshold_mode':'zero'},'processing':{},'source_sha256':source,'image_info':{'channel_labels':['A']},'results':[{'roi':{'id':'r'},'channel_summary':[{'channel':0,'mean':offset+experiment}]}]}
            items.append({'status':'completed','condition':condition,'experiment':str(experiment),'cell':'c','image_id':source,'result':result})
    opts=ExperimentRequest(run_id='r',conditions=['a','b'],metric='mean',design='paired_experiments',normal_model=True,iterations=199)
    r=analyze_experiment({'id':'r','items':items},opts);c=r['contrasts'][0]
    assert c['analysis_mode']=='estimation_only' and not c['significance_attainable']
    assert c['hierarchical_bootstrap_ci95'] is None and c['exact_probability_floor']==.25
    assert r['groups'][0]['sample_sd']==pytest.approx(1)
    assert r['groups'][0]['normal_mle_sigma']==pytest.approx(np.sqrt(2/3))
    assert analyze_experiment({'id':'r','items':items},opts.model_copy(update={'exploratory_intervals':True}))['contrasts'][0]['hierarchical_bootstrap_ci95'] is not None
