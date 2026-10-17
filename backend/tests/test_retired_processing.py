import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.processing import ProcessingConfig
from organelle_scope.experiments import ExperimentRequest,analyze_experiment

def test_removed_routes_and_no_silent_legacy_processing(tmp_path):
    with TestClient(create_app(tmp_path,'test')) as client:
        h={'X-Session-Token':'test'}
        assert client.get('/api/restoration/status',headers=h).status_code==404
        assert client.post('/api/restoration/train',headers=h,json={}).status_code==404
        assert client.post('/api/restoration/deconvolve',headers=h,json={}).status_code==404
    with pytest.raises(ValidationError,match='were removed'):ProcessingConfig(restoration_result_id='12345678-1234-1234-1234-123456789012')
    assert ProcessingConfig(background='rolling_ball',sigma_px=1).active

def test_recovery_preserves_historical_reports_before_replacing_copy(tmp_path):
    with TestClient(create_app(tmp_path/'images','test')) as client:
        h={'X-Session-Token':'test'};old={'name':'Historical','state':{'core':{'processing':{'restoration_result_id':'12345678-1234-1234-1234-123456789012'}},'results':{'sum':123}}}
        assert client.post('/api/recovery',headers=h,json=old).status_code==200
        assert client.post('/api/recovery',headers=h,json={'name':'New','state':{'core':{}}}).status_code==200
        projects=client.get('/api/projects',headers=h).json();assert len(projects)==1
        saved=client.get('/api/projects/'+projects[0]['id'],headers=h).json();assert saved['state']==old['state']

def test_historical_restored_batch_cannot_drive_new_inference():
    run={'id':'old','items':[{'condition':'a','experiment':'e','cell':'c','status':'completed','result':{'request':{'threshold_mode':'zero','processing':{'restoration_result_id':'old'}},'processing':{}}}]}
    options=ExperimentRequest(run_id='old',conditions=['a','b'],design='independent_experiments')
    with pytest.raises(ValueError,match='retired denoising/deconvolution'):analyze_experiment(run,options)
    assert run['items'][0]['result']['request']['processing']['restoration_result_id']=='old'
