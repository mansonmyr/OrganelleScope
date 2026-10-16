import json
import pytest
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.assistant import ChatRequest,run_agent

RECORD={'id':'11111111-1111-1111-1111-111111111111','name':'Test','revision':3,'image':None,'state':{'core':{},'workspaces':{}}}

def response(content='',name=None,args='{}'):
 message={'role':'assistant','content':content}
 if name:message['tool_calls']=[{'id':'call1','type':'function','function':{'name':name,'arguments':args}}]
 return {'choices':[{'message':message,'finish_reason':'stop'}],'usage':{'completion_tokens':8}}

class Fake:
 def __init__(self,*replies):self.replies=iter(replies);self.messages=[]
 def completion(self,messages,tools,response_format=None):self.messages.append(json.loads(json.dumps(messages)));return next(self.replies)

def options(**kw):return ChatRequest(project_id=RECORD['id'],message='Assess the saved project',**kw)

def test_agent_executes_reference_tools_and_exposes_audit():
 model=Fake(response(name='inspect_project'),response(name='run_reference_checks'),response('No biological validation is established. [project] [reference]'))
 result=run_agent(model,RECORD,options(),None)
 assert [a['tool'] for a in result['audit']]==['inspect_project','inspect_project','run_reference_checks']
 assert result['audit'][2]['result']['report']['passed']
 assert result['project_revision']==3
 assert model.messages[1][-1]['role']=='tool'

@pytest.mark.parametrize('reply,match',[(response(name='shell'),'unsupported'),(response(name='inspect_project',args='{"path":"/etc/passwd"}'),'invalid tool arguments'),(response('See [invented-1]'),'unverified|Expecting value'),(response('See https://example.com'),'unverified|Expecting value')])
def test_agent_rejects_unapproved_tools_arguments_and_citations(reply,match):
 with pytest.raises(ValueError,match=match):run_agent(Fake(reply,reply),RECORD,options(),None)


def test_agent_budget_stops_repeated_tools():
 with pytest.raises(ValueError,match='four-tool limit'):
  run_agent(Fake(*[response(name='inspect_project') for _ in range(5)]),RECORD,options(),None)


def test_evidence_refresh_uses_only_saved_query_and_offline_by_default():
 record=json.loads(json.dumps(RECORD));record['state']['workspaces']={'EvidencePanel.academic':True,'EvidencePanel.result':{'query':{'provider':'kegg','operation':'pathways','identifiers':['hsa:5116']}}}
 calls=[]
 def query(request):calls.append(request);return {'provider':'kegg','rows':[],'sources':[{'source_url':'https://rest.kegg.jp/link/pathway/hsa:5116','retrieved_utc':'today','response_sha256':'a'*64}]}
 result=run_agent(Fake(response(name='refresh_selected_evidence'),response('No measured activation. [evidence-1-1]')),record,options(),query)
 assert calls[0].offline_only and calls[0].academic_use and calls[0].identifiers==['hsa:5116']
 assert result['sources'][-1]['url'].startswith('https://rest.kegg.jp/')


def test_assistant_auth_status_and_no_implicit_download(tmp_path,monkeypatch):
 monkeypatch.setenv('ORGANELLESCOPE_MODEL',str(tmp_path/'missing.gguf'))
 monkeypatch.setenv('ORGANELLESCOPE_LLAMA_SERVER',str(tmp_path/'missing-server'))
 with TestClient(create_app(tmp_path/'images','token')) as client:
  assert client.get('/api/assistant/status').status_code==401
  h={'X-Session-Token':'token'}
  assert client.get('/api/assistant/status',headers=h).json()['model_available'] is False
  assert client.post('/api/assistant/start',headers=h).status_code==422
  assert client.post('/api/assistant/chat',headers=h,json={'project_id':RECORD['id'],'message':'hello','endpoint':'https://example.com'}).status_code==422
 assert not (tmp_path/'missing.gguf').exists()


def test_generated_quantities_are_repaired_or_withheld_instead_of_becoming_measurements():
 from organelle_scope.assistant import invalid_answer
 assert invalid_answer('The ROI diameter is 20 µm. [project]',{'project':{}})
 assert invalid_answer('The probability is 0.95. [project]',{'project':{}})
 assert not invalid_answer('TP53 and TUBG1 require experimental controls. [project]',{'project':{}})
 model=Fake(response('The ROI diameter is 20 µm. [project]'),response(json.dumps({'answer':'The ROI describes a selected image region; it does not establish binding.','citations':['project']})))
 result=run_agent(model,RECORD,options(),None)
 assert '20' not in result['answer'] and len(model.messages)==2
 with pytest.raises(ValueError,match='quantitative claim'):
  run_agent(Fake(response('Diameter is 20 µm.'),response(json.dumps({'answer':'Diameter is 20 µm.','citations':['project']}))),RECORD,options(),None)


def test_generated_tool_output_is_data_and_only_one_system_message_is_used():
 model=Fake(response(name='read_measurements'),response('No measured results are saved. [measurements]'))
 run_agent(model,RECORD,options(),None)
 assert len([m for m in model.messages[0] if m['role']=='system'])==1
 assert 'Saved project context (untrusted data' in model.messages[0][0]['content']


def test_recorded_values_require_matching_source_and_calibration_provenance():
 from organelle_scope.assistant import recorded_quantities
 record=json.loads(json.dumps(RECORD));record['image']={'sha256':'source','info':{'calibration':{a:{'value_um':v} for a,v in zip('XYZ',[.1,.1,.4])}}}
 record['state']['core']['analysis']={'source_sha256':'different','image_info':record['image']['info'],'results':[{'pixel_count':1257,'area_um2':12.57,'pairs':[{'label_a':'A','label_b':'B','pcc':.9889}]}]}
 assert len(recorded_quantities(record))==3
 record['state']['core']['analysis']['source_sha256']='source'
 facts=recorded_quantities(record)
 assert next(f['value'] for f in facts if f['label'].endswith('area_um2'))==12.57
 assert next(f['value'] for f in facts if f['label'].endswith('pcc'))==.9889


def test_local_model_refuses_modified_weights_before_executing_runtime(tmp_path,monkeypatch):
 from organelle_scope.local_model import LocalModel
 binary=tmp_path/'server';binary.write_bytes(b'not executed')
 weights=tmp_path/'model';weights.write_bytes(b'incomplete')
 monkeypatch.setenv('ORGANELLESCOPE_LLAMA_SERVER',str(binary));monkeypatch.setenv('ORGANELLESCOPE_MODEL',str(weights))
 model=LocalModel(tmp_path/'logs')
 with pytest.raises(ValueError,match='integrity'):model.start()
 assert model.process is None


def test_schema_request_does_not_replace_application_validation():
 # A runtime/model can ignore the requested schema; unknown source IDs remain rejected.
 model=Fake(response('An unsupported value is 20 µm.'),response(json.dumps({'answer':'Qualitative draft','sources':['project']})))
 with pytest.raises(ValueError,match='valid cited draft'):run_agent(model,RECORD,options(),None)
 model=Fake(response('No citation.'),response(json.dumps({'answer':'Qualitative draft','citations':['invented']})))
 with pytest.raises(ValueError,match='valid cited draft'):run_agent(model,RECORD,options(),None)
