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


def test_gemma_request_uses_selected_model_settings(tmp_path,monkeypatch):
 from organelle_scope.local_model import LocalModel,MODEL
 model=LocalModel(tmp_path);monkeypatch.setattr(model,'status',lambda:{'ready':True})
 calls=[];monkeypatch.setattr(model,'_request',lambda path,body,**kwargs:(calls.append((path,body,kwargs)) or {}))
 model.completion([{'role':'user','content':'Test'}])
 assert MODEL['name'].startswith('Gemma') and MODEL['bytes']==6975879296
 assert calls[0][1]['temperature']==1.0 and calls[0][2]['timeout']==300
 assert calls[0][1]['chat_template_kwargs']=={'enable_thinking':False} and calls[0][1]['max_tokens']==1600


def test_bounded_tool_results_keep_source_ids_visible():
 from organelle_scope.assistant import bounded
 result=bounded({'source_ids':['evidence-1-1'],'records':['x'*10000]})
 assert result['truncated'] and result['source_ids']==['evidence-1-1']


def test_interpretation_settings_survive_large_report_truncation():
 from organelle_scope.assistant import bounded,measurement_context
 analysis={'processing':{'settings':{'background':'none'}},'request':{'threshold_mode':'zero'},'results':[{'roi':{'id':'r'},'pairs':[{'thresholds':{'a':0,'b':0},'thresholded_m1':1}]}]}
 result=bounded({'source_id':'measurements','interpretation_context':measurement_context(analysis),'roi':'x'*10000})
 context=result['interpretation_context']
 assert result['truncated'] and context['processing']['background']=='none'
 assert context['threshold_mode']=='zero' and context['pairs'][0]['thresholds']=={'a':0,'b':0}
 assert 'not proof' in context['controls_note']


def test_large_interpretation_context_remains_bounded():
 from organelle_scope.assistant import bounded
 result=bounded({'interpretation_context':{'processing':{'background':'none'},'pairs':['x'*10000]},'roi':'y'*20000})
 assert result['interpretation_context']['truncated']
 assert len(json.dumps(result))<8500


def test_saved_measurement_summary_is_supplied_before_model_answers():
 record=json.loads(json.dumps(RECORD));record['state']['core']['analysis']={'processing':{'settings':{'background':'none'}},'request':{'threshold_mode':'zero'}}
 model=Fake(response('The saved thresholds require sensitivity checks. [measurements]'))
 result=run_agent(model,record,options(),None)
 assert result['audit'][1]['trigger']=='application summary context'
 assert 'Saved measurement summary' in model.messages[0][0]['content']
 assert 'threshold_mode' in model.messages[0][0]['content']


def test_exact_kegg_identifiers_are_not_measurements_and_alterations_are_rejected():
 from organelle_scope.assistant import invalid_answer
 sources={'evidence-1-1':{}}
 assert not invalid_answer('Membership of hsa:7157 does not establish activation. [evidence-1-1]',sources,{'hsa:7157'})
 assert invalid_answer('Membership of hsa:T157 does not establish activation. [evidence-1-1]',sources,{'hsa:7157'})
 assert invalid_answer('Membership of hsa:7158 does not establish activation. [evidence-1-1]',sources,{'hsa:7157'})
 assert invalid_answer('hsa:7157 has a binding probability of 0.95. [evidence-1-1]',sources,{'hsa:7157'})


def test_evidence_gene_identifiers_are_collected_from_actual_tool_records():
 record=json.loads(json.dumps(RECORD));record['state']['workspaces']={'EvidencePanel.result':{'provider':'kegg','rows':[{'gene':'hsa:7157'}],'sources':[{'source_url':'https://rest.kegg.jp/link/pathway/hsa:7157'}]}}
 model=Fake(response(name='read_evidence'),response('hsa:7157 membership is not measured activation. [evidence-1-1]'))
 result=run_agent(model,record,options(),None)
 assert 'hsa:7157' in result['answer']


def test_candidate_model_does_not_change_selected_model_or_response_provenance(tmp_path,monkeypatch):
 from organelle_scope.local_model import LocalModel,MODEL
 from organelle_scope.model_candidates import LIQUID_MODEL
 model=LocalModel(tmp_path,manifest=LIQUID_MODEL);calls=[]
 monkeypatch.setattr(model,'status',lambda:{'ready':True})
 monkeypatch.setattr(model,'_request',lambda path,body,**kwargs:calls.append(body))
 model.completion([{'role':'user','content':'Test'}])
 assert MODEL['name'].startswith('Gemma') and model.model.name==LIQUID_MODEL['filename']
 assert calls[0]['temperature']==.2 and calls[0]['top_k']==80 and calls[0]['repeat_penalty']==1.05
 assert calls[0]['chat_template_kwargs']['enable_thinking'] is True
 fake=Fake(response('No image is saved. [project]'));fake.manifest=LIQUID_MODEL
 assert run_agent(fake,RECORD,options(),None)['model']['sha256']==LIQUID_MODEL['sha256']


@pytest.mark.parametrize('quantity',['20-pixel','20‑pixel','20–pixel','２０‑pixel'])
def test_hyphenated_numeric_quantities_cannot_evade_qualitative_prose_guard(quantity):
 from organelle_scope.assistant import invalid_answer
 assert invalid_answer('An applied '+quantity+' filter establishes binding. [measurements]',{'measurements':{}})


def test_quantity_normalization_keeps_protein_names_dimensions_and_exact_ids():
 from organelle_scope.assistant import invalid_answer
 assert not invalid_answer('TP53, 53BP1 and 3D measurements require review. [project]',{'project':{}})
 assert not invalid_answer('hsa:7157 membership is not activation. [project]',{'project':{}},{'hsa:7157'})


def test_questions_without_project_start_local_model_and_do_not_save(tmp_path,monkeypatch):
 import organelle_scope.assistant as module
 calls=[]
 class ReadyFake(Fake):
  def __init__(self,*a):super().__init__(response('General microscopy advice is available without an image. [project]'));self.ready=False;self.manifest={'bytes':1};self.model=tmp_path/'missing.gguf';self.binary=tmp_path/'missing-runtime'
  def status(self):return {'ready':self.ready,'running':self.ready,'model_available':False}
  def start(self):calls.append('start');self.ready=True
  def stop(self):pass
  def cleanup_after_success(self):pass
 monkeypatch.setattr(module,'LocalModel',ReadyFake)
 with TestClient(create_app(tmp_path/'images','token')) as client:
  answer=client.post('/api/assistant/chat',headers={'X-Session-Token':'token'},json={'message':'What does correlation mean?','allow_online':False})
  assert answer.status_code==200,answer.text
  result=answer.json();assert result['project_id'] is None and result['project_revision'] is None
  assert result['context_kind']=='workspace' and result['audit'][0]['result']['image'] is None
  assert calls==['start'] and not list((tmp_path/'project-data').glob('*.json'))


def test_workspace_context_uses_unsaved_settings_and_excludes_stale_measurements():
 from organelle_scope.assistant import WorkspaceContext,workspace_record
 image={'id':'11111111-1111-1111-1111-111111111111','sha256':'source','info':{'filename':'current.tif','dimensions':{'C':2},'calibration':{a:{'value_um':.1} for a in 'XYZ'}}}
 report={'source_sha256':'source','image_info':image['info'],'request':{'threshold_mode':'manual','thresholds':[42,51]},'results':[]}
 context=WorkspaceContext(image_id=image['id'],expected_image_info=image['info'],state={'core':{'thresholdMode':'manual','thresholds':[42,51],'analysis':report},'workspaces':{'EvidencePanel.offline':True,'AssistantPanel.turns':['large conversation']}})
 record=workspace_record(context,lambda _: (None,image,None))
 assert record['state']['core']['thresholds']==[42,51]
 assert record['state']['core']['analysis']==report
 assert 'AssistantPanel.turns' not in record['state']['workspaces']
 model=Fake(response('Inspect the current manual thresholds before interpreting overlap. [project]'))
 result=run_agent(model,record,ChatRequest(message='Explain these settings',context=context),None)
 assert result['context_kind']=='workspace' and result['project_revision'] is None
 assert model.messages[0][0]['content'].find('Current workspace snapshot')>=0
 context.expected_image_info={}
 stale=workspace_record(context,lambda _: (None,image,None))
 assert stale['state']['core']['analysis'] is None and 'calibration changed' in stale['context_note']
 assert context.state['core']['analysis']==report  # never mutate caller's results


def test_offline_current_evidence_never_requires_academic_permission_for_model():
 from organelle_scope.assistant import WorkspaceContext,workspace_record
 context=WorkspaceContext(state={'workspaces':{'EvidencePanel.academic':False,'EvidencePanel.offline':True}})
 record=workspace_record(context,None)
 def forbidden(_):pytest.fail('No lookup should be needed for a local question')
 result=run_agent(Fake(response('I can explain general methodology without an online lookup. [project]')),record,ChatRequest(message='Explain microscopy',context=context),forbidden)
 assert 'methodology' in result['answer']


def test_general_workspace_advice_does_not_need_invented_project_citation():
 from organelle_scope.assistant import workspace_record
 record=workspace_record(None,None)
 answer=run_agent(Fake(response('General advice: correlation describes intensity association and does not establish binding.')),record,ChatRequest(message='What does correlation mean?'),None)
 assert answer['context_kind']=='workspace' and 'General advice' in answer['answer']
 with pytest.raises(ValueError):
  run_agent(Fake(response('See [invented]'),response('not JSON')),record,ChatRequest(message='Test'),None)


def test_recorded_channel_and_roi_labels_are_identifiers_not_generated_quantities():
 from organelle_scope.assistant import invalid_answer
 identifiers={'Channel 3','Alexa Fluor 488','ROI 1'};sources={'measurements':{}}
 assert not invalid_answer('Channel 3 is constant in ROI 1; Alexa Fluor 488 needs a control. [measurements]',sources,identifiers)
 assert invalid_answer('The distance is 3 µm. [measurements]',sources,identifiers)
 assert invalid_answer('Channel 4 is empty. [measurements]',sources,identifiers)
 assert invalid_answer('The width is 20 pixels. [measurements]',sources,{'20 pixels'})


def test_agent_accepts_a_real_channel_label_from_the_supplied_image():
 record=json.loads(json.dumps(RECORD))
 record['image']={'sha256':'source','info':{'channel_labels':['Channel 1','Channel 2','Channel 3'],'calibration':{a:{'value_um':None} for a in 'XYZ'}}}
 model=Fake(response('Channel 3 needs its acquired signal checked; absence from the image is not proof of biological absence. [project]'))
 result=run_agent(model,record,options(),None)
 assert 'Channel 3' in result['answer'] and len(model.messages)==1


def test_null_metrics_in_completed_report_are_not_described_as_unperformed():
 from organelle_scope.assistant import measurement_context,bounded
 analysis={'processing':{'settings':{'background':'none'}},'request':{'threshold_mode':'costes'},'results':[{'roi':{'id':'r'},'channel_summary':[{'label':'Channel 1','sum':40,'std':2},{'label':'Channel 3','sum':0,'std':0}],'pairs':[{'pcc':None,'warnings':['constant channel'],'thresholds':{'status':'constant','a':None,'b':None}}]}]}
 context=measurement_context(analysis)
 assert context['calculation_completed'] is True and 'NOT evidence' in context['null_semantics']
 assert context['constant_channels'][0]['label']=='Channel 3' and context['constant_channels'][0]['all_zero'] is True
 assert 'cannot repair' in context['constant_channels'][0]['explanation']
 wrapped=bounded({'interpretation_context':context,'roi':'x'*20000})
 assert wrapped['interpretation_context']['constant_channels'][0]['all_zero'] is True


def test_assistant_reads_matching_segmentation_and_batch_context_without_tool_request():
 from organelle_scope.interpretation import interpretation_snapshot
 record=json.loads(json.dumps(RECORD))
 info={'calibration':{a:{'value_um':.1} for a in 'XYZ'},'channel_labels':['Marker A','Marker B']}
 record['image']={'sha256':'source','info':info}
 report={'source_sha256':'source','image_info':info,'object_count':2,'foreground_voxels':10,'objects':[{'touches_cuboid_edge':True},{'touches_cuboid_edge':False}],'proximity':{'fraction_marker_voxels_within_distance':.6},'request':{'channel':0}}
 record['state']['workspaces']={'Segmentation.report':report,'ExperimentPanel.runId':'batch','ExperimentPanel.report':{'request':{'run_id':'batch'},'groups':[{'condition':'control','independent_experiments':3}],'contrasts':[]}}
 snapshot=interpretation_snapshot(record)
 assert snapshot['reports']['segmentation']['objects_touching_cuboid_edge']==1
 assert snapshot['reports']['experiment']['groups'][0]['independent_experiments']==3
 model=Fake(response('The mask defines image foreground rather than binding. [interpretation]'))
 result=run_agent(model,record,options(),None)
 assert 'foreground_voxels' in model.messages[0][0]['content']
 assert any('batch' in n for n in result['interpretation_notes'])
 report['source_sha256']='wrong'
 assert 'segmentation' not in interpretation_snapshot(record)['reports']
 record['state']['workspaces']['ExperimentPanel.runId']='other'
 assert 'experiment' not in interpretation_snapshot(record)['reports']


def test_selected_cached_evidence_is_supplied_without_online_access_or_model_tool():
 record=json.loads(json.dumps(RECORD));record['state']['workspaces']={'EvidencePanel.result':{'provider':'kegg','rows':[{'gene':'hsa:7157','pathway':'hsa04115'}],'sources':[{'source_url':'https://rest.kegg.jp/link/pathway/hsa:7157'}]}}
 def forbidden(_):pytest.fail('Cached context must not trigger network access')
 model=Fake(response('hsa:7157 pathway membership does not establish activation. [evidence-1-1]'))
 result=run_agent(model,record,options(),forbidden)
 assert 'hsa04115' in model.messages[0][0]['content']
 assert any(a.get('trigger')=='application selected evidence' for a in result['audit'])


def test_workspace_excludes_stale_segmentation_and_quality():
 from organelle_scope.assistant import WorkspaceContext,workspace_record
 image={'sha256':'s','info':{'filename':'synthetic.tif'}}
 context=WorkspaceContext(image_id='11111111-1111-1111-1111-111111111111',expected_image_info=image['info'],state={'workspaces':{'Segmentation.report':{'source_sha256':'wrong','image_info':image['info']},'ChannelPanel.quality':{'source_sha256':'s','image_info':{}}}})
 record=workspace_record(context,lambda _:(None,image,None))
 assert not record['state']['workspaces']


def test_interpretation_notes_distinguish_zero_signal_and_rgb_display_components():
 from organelle_scope.interpretation import interpretation_snapshot
 record={'image':{'info':{'acquisition':{'stored_color_model':'RGB components'}}},'state':{'core':{'analysis':{'results':[{'channel_summary':[{'label':'A','std':0,'sum':0}]}]}}}}
 notes=interpretation_snapshot(record)['notes']
 assert any('RGB components' in n for n in notes)
 assert any('all zero' in n and 'High-intensity saturation is not an explanation' in n for n in notes)


def test_acquisition_notes_do_not_reuse_a_different_z_plane_as_current():
 from organelle_scope.interpretation import interpretation_snapshot
 info={'calibration':{}}
 record={'image':{'sha256':'s','info':info},'state':{'core':{'z':2},'workspaces':{'ChannelPanel.quality':{'source_sha256':'s','image_info':info,'z':1,'channels':[]}}}}
 snapshot=interpretation_snapshot(record)
 assert 'acquisition' not in snapshot['reports']
 assert any('different Z plane' in n for n in snapshot['notes'])
 record['state']['core']['z']=1
 assert 'acquisition' in interpretation_snapshot(record)['reports']


def test_directional_context_and_recorded_quantities_follow_engine_marker_order():
 from organelle_scope.assistant import measurement_context,recorded_quantities
 analysis={'source_sha256':'source','image_info':{'calibration':{}},'results':[{'roi':{'id':'r'},'pairs':[{'label_a':'Marker A','label_b':'Marker B','thresholded_m1':1.,'thresholded_m2':.1}]}]}
 definitions=measurement_context(analysis)['pairs'][0]['direction_definitions']
 assert definitions['m1'].startswith('Marker A intensity where Marker B')
 assert definitions['m2'].startswith('Marker B intensity where Marker A')
 record={'image':{'sha256':'source','info':{'calibration':{a:{'value_um':None} for a in 'XYZ'}}},'state':{'core':{'analysis':analysis}}}
 analysis['image_info']=record['image']['info']
 facts=recorded_quantities(record)
 assert any(f['value']==1 and 'M1 · Marker A intensity where Marker B' in f['label'] for f in facts)
 assert any(f['value']==.1 and 'M2 · Marker B intensity where Marker A' in f['label'] for f in facts)


def test_recorded_summary_needs_no_model_and_generation_failure_keeps_engine_notes(tmp_path,monkeypatch):
 import organelle_scope.assistant as module
 def unavailable(*args,**kwargs):
  kwargs['audit_sink'].append({'tool':'inspect_project','result':{'source_id':'project'}})
  raise ValueError('Generated claims could not be substantiated; draft withheld.')
 monkeypatch.setattr(module,'ensure_ready',lambda _:None)
 monkeypatch.setattr(module,'run_agent',unavailable)
 with TestClient(create_app(tmp_path/'images','token')) as client:
  payload={'message':'Interpret the current measurements','context':{'state':{'core':{},'workspaces':{}}}}
  assert client.post('/api/assistant/notes',json=payload).status_code==401
  response=client.post('/api/assistant/notes',headers={'X-Session-Token':'token'},json=payload)
  assert response.status_code==200
  notes=response.json();assert notes['response_mode']=='application_summary' and notes['model'] is None
  assert notes['generation_error'] is None and notes['interpretation_notes']
  response=client.post('/api/assistant/chat',headers={'X-Session-Token':'token'},json=payload)
  assert response.status_code==200
  fallback=response.json();assert fallback['response_mode']=='application_summary'
  assert 'withheld' in fallback['generation_error']
  assert [a['tool'] for a in fallback['audit']]==['inspect_project','application_summary']


def test_session_readiness_requires_application_token(tmp_path):
 with TestClient(create_app(tmp_path,'test')) as client:
  assert client.get('/api/ready').status_code==401
  assert client.get('/api/ready',headers={'X-Session-Token':'wrong'}).status_code==401
  response=client.get('/api/ready',headers={'X-Session-Token':'test'})
  assert response.status_code==200 and response.json()['status']=='ok'


def test_proximity_reading_notes_explain_empty_masks_and_existing_reverse_summary():
 from organelle_scope.interpretation import interpretation_snapshot
 from organelle_scope.assistant import recorded_quantities
 info={'calibration':{a:{'value_um':1} for a in 'XYZ'},'channel_labels':['A','B']}
 image={'info':info,'sha256':'source'}
 record={'image':image,'state':{'core':{},'workspaces':{'Segmentation.report':{'source_sha256':'source','image_info':info,'proximity':{'unavailable_reason':'Reference mask is empty.'}}}}}
 reading=interpretation_snapshot(record)
 assert any('undefined distance/fraction is not zero probability' in n for n in reading['notes'])
 assert any('fraction is undefined rather than zero' in f for f in reading['findings'])
 direction={'source_voxels':2,'fraction_within_distance':.5,'median_occupied_voxel_center_um':2}
 record['state']['workspaces']['Segmentation.report']['proximity']={'marker_to_reference':direction,'reference_to_marker':{**direction,'source_voxels':1,'fraction_within_distance':1},'distance_threshold_um':.5}
 assert any('Both proximity directions are already recorded' in n for n in interpretation_snapshot(record)['notes'])
 facts=recorded_quantities(record)
 assert any(f['value']==.5 and 'Marker → reference' in f['label'] for f in facts)
 assert any(f['value']==1 and 'Reference → marker' in f['label'] for f in facts)
 record['image']['sha256']='changed'
 assert not any('Cuboid proximity' in f['label'] for f in recorded_quantities(record))


@pytest.mark.parametrize('malformed',[False,True])
def test_generated_draft_has_separate_nonblocking_question_coverage(malformed):
 answer='Pearson measures linear intensity correlation. [methods]'
 claim={'claims':[{'index':0,'kind':'record_supported','source_id':'methods','quote':'Pearson is centered linear intensity correlation.'}]}
 coverage={'coverage':[{'index':0,'status':'addressed','answer_quote':'Pearson measures linear intensity correlation.'},{'index':1,'status':'unanswered','answer_quote':''}]}
 model=Fake(response(answer),response(json.dumps(claim)),response('not json' if malformed else json.dumps(coverage)));model.manifest={'name':'test','evidence_review':True}
 result=run_agent(model,RECORD,ChatRequest(message='What does Pearson measure? Does it prove binding?'),None)
 assert result['answer']==answer
 assert result['question_coverage']['assessed'] is (not malformed)
 assert not result['question_coverage']['all_parts_addressed']
