"""Recovery preserves frozen runs; reports and jobs retain authoritative source scope."""
import json
import time
from threading import Event
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from test_batch import upload,item,wait,H


def wait_job(client,ident):
    for _ in range(300):
        value=client.get('/api/analysis-jobs/'+ident,headers=H).json()
        if value['status'] not in ('running','cancelling'):return value
        time.sleep(.01)
    pytest.fail('job did not finish')


def test_roi_job_matches_sync_and_reports_steps(tmp_path):
    with TestClient(create_app(tmp_path,'token')) as client:
        image=upload(client);options=item(image)['analysis']
        expected=client.post('/api/images/'+image['id']+'/analysis',headers=H,json=options).json()
        start=client.post('/api/images/'+image['id']+'/analysis-jobs',headers=H,json=options)
        assert start.status_code==200,start.text
        job=wait_job(client,start.json()['id'])
        assert job['status']=='completed' and {k:v for k,v in job['result'].items() if k not in ('report_id','created_utc')}=={k:v for k,v in expected.items() if k not in ('report_id','created_utc')}
        assert job['progress']['total']==3 and job['progress']['completed']==3
        assert client.get('/api/analysis-jobs/'+job['id']).status_code==401


def test_cancel_roi_job_keeps_previous_results(tmp_path,monkeypatch):
    import organelle_scope.analysis_jobs as module
    entered=Event();release=Event();real=module.compute_analysis
    def barrier(*args):entered.set();release.wait(3);return real(*args)
    with TestClient(create_app(tmp_path,'token')) as client:
        image=upload(client);options=item(image)['analysis']
        url='/api/images/'+image['id']
        original=client.post(url+'/analysis',headers=H,json=options).json()
        monkeypatch.setattr(module,'compute_analysis',barrier)
        job=client.post(url+'/analysis-jobs',headers=H,json=options).json();assert entered.wait(3)
        assert client.post(url+'/analysis-jobs',headers=H,json=options).status_code==409
        client.post('/api/analysis-jobs/'+job['id']+'/cancel',headers=H);release.set()
        assert wait_job(client,job['id'])['status']=='cancelled'
        assert client.get(url+'/analysis',headers=H).json()==original


def test_portable_review_links_geometry_engine_values_and_rejects_changed_source(tmp_path):
    with TestClient(create_app(tmp_path,'token')) as client:
        image=upload(client,'<img onerror=alert(1)>.tif');url='/api/images/'+image['id']
        options=item(image)['analysis'];result=client.post(url+'/analysis',headers=H,json=options).json()
        context={'image_id':image['id'],'expected_image_info':image['info'],'state':{'core':{'areas':result['request']['rois'],'analysis':result},'workspaces':{}}}
        report=client.post(url+'/review-report',headers=H,json=context)
        assert report.status_code==200,report.text
        assert 'href="#roi-0"' in report.text and '<ellipse ' in report.text and 'data:image/png;base64,' in report.text
        assert str(result['results'][0]['pixel_count'])+' pixels' in report.text
        assert '<img onerror' not in report.text and '&lt;img onerror' in report.text and 'Channel A / B' in report.text
        changed=deepcopy(context);changed['state']['core']['analysis']['results'][0]['pairs'][0]['pcc']=.12345
        assert 'No matching ROI results' in client.post(url+'/review-report',headers=H,json=changed).text
        context['expected_image_info']={}
        assert client.post(url+'/review-report',headers=H,json=context).status_code==409
        context['expected_image_info']=image['info'];(tmp_path/image['id']/'source.tiff').write_bytes(b'changed')
        assert client.post(url+'/review-report',headers=H,json=context).status_code==409


def test_recovery_draft_preserves_old_successes_and_revalidates_metadata(tmp_path):
    with TestClient(create_app(tmp_path,'token')) as client:
        a,b=upload(client),upload(client,'failed.tif')
        saved=client.post('/api/batch/sessions',headers=H,json={'name':'original','items':[item(a),item(b)]}).json()
        source=tmp_path/b['id']/'source.tiff';raw=source.read_bytes();source.write_bytes(b'changed')
        run=client.post('/api/batch/runs',headers=H,json={'session_id':saved['id'],'revision':1}).json();old=wait(client,run['id'])
        assert old['status']=='completed_with_errors'
        client.post('/api/images/'+b['id']+'/channels',headers=H,json={'labels':['Correct A','Correct B'],'expected_image_info':b['info']})
        recovery=client.post('/api/batch/runs/'+run['id']+'/retry-draft',headers=H).json()
        assert len(recovery['items'])==1 and recovery['items'][0]['image_id']==b['id']
        assert not recovery['items'][0]['reviewed'] and recovery['retry_of_run_id']==old['id']
        assert recovery['items'][0]['analysis']==old['items'][1]['analysis']
        assert client.get('/api/batch/runs/'+run['id'],headers=H).json()==old
        source.write_bytes(raw);recovery['items'][0]['reviewed']=True
        revised=client.post('/api/batch/sessions/'+recovery['id'],headers=H,json={**recovery,'revision':1}).json()
        started=client.post('/api/batch/runs',headers=H,json={'session_id':revised['id'],'revision':2}).json()
        done=wait(client,started['id']);assert done['status']=='completed' and done['retry_of_run_id']==old['id']
        assert client.post('/api/batch/runs/'+done['id']+'/retry-draft',headers=H).status_code==422


def test_shared_tiff_reader_opens_directory_once_per_analysis(tmp_path,monkeypatch):
    import organelle_scope.analysis_service as module
    from organelle_scope.image_io import ImageInfo
    from organelle_scope.roi_analysis import AnalysisRequest
    with TestClient(create_app(tmp_path,'token')) as client:image=upload(client)
    original=module.tifffile.TiffFile;opens=[]
    def counted(*args,**kwargs):opens.append(args[0]);return original(*args,**kwargs)
    monkeypatch.setattr(module.tifffile,'TiffFile',counted)
    options=item(image)['analysis'];options['rois']+= [{**options['rois'][0],'id':'other','z':2}]
    values=[]
    result=module.compute_analysis(tmp_path/image['id'],image,ImageInfo.model_validate(image['info']),AnalysisRequest.model_validate(options),progress=lambda **v:values.append(v))
    assert len(opens)==1 and len(result['results'])==2 and values[-1]['completed']==6


def test_assistant_excludes_edited_rois_and_stale_auxiliary_sweeps():
    from organelle_scope.assistant import WorkspaceContext,workspace_record
    image={'id':'11111111-1111-1111-1111-111111111111','sha256':'raw','info':{'filename':'test.tif','dimensions':{'C':2}}}
    report={'source_sha256':'raw','image_info':image['info'],'request':{'rois':[{'id':'old'}]}}
    context=WorkspaceContext(image_id=image['id'],expected_image_info=image['info'],state={'core':{'areas':[{'id':'new'}],'analysis':report},'workspaces':{'Segmentation.sensitivity':{'source_sha256':'another','image_info':image['info']}}})
    record=workspace_record(context,lambda _: (None,image,None))
    assert record['state']['core']['analysis'] is None
    assert 'Segmentation.sensitivity' not in record['state']['workspaces']
    assert context.state['core']['analysis']==report
