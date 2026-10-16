import io,json
import numpy as np
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app

H={'X-Session-Token':'token'}

def image(client):
 stream=io.BytesIO();tifffile.imwrite(stream,np.arange(2*3*8*9,dtype='uint16').reshape(2,3,8,9),ome=True,photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':.4})
 return client.post('/api/images',headers=H,files={'file':('project.ome.tif',stream.getvalue())}).json()


def test_complete_project_round_trip_conflicts_and_session_auth(tmp_path):
 folder=tmp_path/'images'
 with TestClient(create_app(folder,'token')) as client:
  record=image(client)
  state={'core':{'z':2,'areas':[{'id':'roi','kind':'circle','z':2,'center':{'x':4,'y':4},'radius':2}],'processing':{'background':'constant','offsets':[1,2]}},'workspaces':{'ValidationPanel.spatial':{'seed':1729,'p_value':.02},'OrthogonalWorkspace.report':{'volume_um3':12.3},'EvidencePanel.result':{'rows':[]},'AssistantPanel.turns':[{'question':'What is missing?'}]}}
  body={'name':'Experiment A','image_id':record['id'],'expected_image_info':record['info'],'state':state}
  assert client.post('/api/projects',json=body).status_code==401
  saved=client.post('/api/projects',headers=H,json=body).json();pid=saved['id']
  assert saved['revision']==1 and saved['state']==state
  assert client.post('/api/projects/'+pid,headers=H,json=body).status_code==409
  updated=client.post('/api/projects/'+pid,headers=H,json={**body,'name':'Renamed','expected_revision':1}).json()
  assert updated['revision']==2
  assert client.post('/api/projects/'+pid,headers=H,json={**body,'expected_revision':1}).status_code==409
 with TestClient(create_app(folder,'token')) as client:
  reopened=client.get('/api/projects/'+pid,headers=H).json()
  assert reopened['state']==state and reopened['image']['sha256']==record['sha256']
  assert client.get('/api/projects',headers=H).json()[0]['name']=='Renamed'


def test_project_restores_its_calibration_without_overwriting_other_import(tmp_path):
 with TestClient(create_app(tmp_path/'images','token')) as client:
  record=image(client);iid=record['id']
  saved=client.post('/api/projects',headers=H,json={'name':'Original calibration','image_id':iid,'expected_image_info':record['info'],'state':{}}).json()
  client.post('/api/images/'+iid+'/inspect',headers=H,json={'spacing_um':{'X':.25}})
  opened=client.get('/api/projects/'+saved['id'],headers=H).json()
  assert opened['image']['id']!=iid
  assert opened['image']['info']['calibration']['X']['value_um']==.1
  assert client.get('/api/images/'+iid,headers=H).json()['info']['calibration']['X']['value_um']==.25
  assert client.get('/api/projects/'+saved['id'],headers=H).json()['image']['id']==opened['image']['id']


def test_changed_source_rejected_and_atomic_snapshot_left_intact(tmp_path):
 with TestClient(create_app(tmp_path/'images','token')) as client:
  record=image(client)
  saved=client.post('/api/projects',headers=H,json={'name':'Original','image_id':record['id'],'expected_image_info':record['info'],'state':{}}).json()
  path=tmp_path/'images'/record['id']/'source.tiff'
  path.write_bytes(path.read_bytes()+b'changed')
  assert client.get('/api/projects/'+saved['id'],headers=H).status_code==409
  assert client.post('/api/projects',headers=H,json={'name':' ','state':{}}).status_code==422
  assert not list((tmp_path/'project-data').glob('*.tmp'))


def test_project_save_rejects_metadata_changed_by_another_window(tmp_path):
 with TestClient(create_app(tmp_path/'images','token')) as client:
  record=image(client)
  body={'name':'Old UI settings','image_id':record['id'],'expected_image_info':record['info'],'state':{}}
  client.post('/api/images/'+record['id']+'/inspect',headers=H,json={'spacing_um':{'X':.25}})
  assert client.post('/api/projects',headers=H,json=body).status_code==409
  assert client.get('/api/projects',headers=H).json()==[]


def test_unreadable_project_and_missing_source_fail_explicitly(tmp_path):
 with TestClient(create_app(tmp_path/'images','token')) as client:
  record=image(client);saved=client.post('/api/projects',headers=H,json={'name':'Recovery','image_id':record['id'],'expected_image_info':record['info'],'state':{}}).json()
  source=tmp_path/'images'/record['id']/'source.tiff';source.rename(source.with_suffix('.backup'))
  response=client.get('/api/projects/'+saved['id'],headers=H)
  assert response.status_code==404 and 'missing' in response.json()['detail']
  (tmp_path/'project-data'/(saved['id']+'.json')).write_text('{broken')
  response=client.get('/api/projects/'+saved['id'],headers=H)
  assert response.status_code==422 and 'backup' in response.json()['detail']
