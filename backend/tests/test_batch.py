import io
import json
import time
from threading import Event
from zipfile import ZipFile
from xml.etree import ElementTree as ET

import numpy as np
import pytest
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.roi_analysis import AreaROI, roi_mask
from organelle_scope.image_io import ImageError
from organelle_scope.excel_export import workbook

H={'X-Session-Token':'token'}


def upload(client,name='image.tif'):
    buf=io.BytesIO()
    source=np.arange(2*3*24*28,dtype=np.uint16).reshape(2,3,24,28)
    tifffile.imwrite(buf,source,ome=True,photometric='minisblack',metadata={'axes':'CZYX','PhysicalSizeX':.2,'PhysicalSizeY':.4,'PhysicalSizeZ':.6})
    r=client.post('/api/images',headers=H,files={'file':(name,buf.getvalue())});assert r.status_code==200,r.text
    return r.json()


def item(image,reviewed=True,diameter=2,z=1):
    return {'image_id':image['id'],'analysis':{'rois':[{'id':'circle','kind':'circle','z':z,'diameter_um':diameter,'points':[{'x':14,'y':12},{'x':19,'y':12}]}], 'threshold_mode':'zero'},'reviewed':reviewed,'experiment':'E1','cell':'C1','condition':'=HYPERLINK("invalid")'}


def wait(client,ident):
    for _ in range(200):
        value=client.get('/api/batch/runs/'+ident,headers=H).json()
        if value['status'] not in ('running','cancelling'):return value
        time.sleep(.01)
    pytest.fail('batch did not complete')


def test_physical_circle_anisotropic_exact_mask_and_legacy():
    roi=AreaROI(id='c',kind='circle',z=0,diameter_um=2,points=[{'x':10,'y':10},{'x':15,'y':10}])
    mask,warnings=roi_mask(roi,(21,21),(.2,.4));y,x=np.indices((21,21))
    expected=((x-10)*.2)**2+((y-10)*.4)**2<=1+1e-12
    np.testing.assert_array_equal(mask,expected);assert not warnings
    assert mask[10,15] and not mask[13,10]
    with pytest.raises(ImageError,match='calibration'):roi_mask(roi,(21,21))
    edge=roi.model_copy(update={'points':[roi.points[0].model_copy(update={'x':0}),roi.points[1].model_copy(update={'x':500})]})
    assert roi_mask(edge,(21,21),(.2,.4))[1]
    legacy=roi.model_copy(update={'diameter_um':None})
    assert roi_mask(legacy,(21,21))[0].sum()>mask.sum()


def test_batch_review_snapshot_excel_failure_and_independent_rois(tmp_path):
    with TestClient(create_app(tmp_path,'token')) as client:
        a,b,c=upload(client),upload(client,'second.tif'),upload(client,'bad.tif')
        draft={'name':'Batch 30','items':[item(a,False),item(b,diameter=3,z=2),item(c)]}
        draft['items'][1]['analysis']['processing']={'background':'constant','offsets':[10,20],'sigma_px':.5}
        saved=client.post('/api/batch/sessions',headers=H,json=draft).json();sid=saved['id']
        run_args={'session_id':sid,'revision':saved['revision']}
        assert client.post('/api/batch/runs',headers=H,json=run_args).status_code==422
        draft.update(revision=saved['revision']);draft['items'][0]['reviewed']=True
        saved=client.post('/api/batch/sessions/'+sid,headers=H,json=draft).json()
        assert client.post('/api/batch/sessions/'+sid,headers=H,json=draft).status_code==409
        (tmp_path/c['id']/'source.tiff').write_bytes(b'tampered')
        response=client.post('/api/batch/runs',headers=H,json={'session_id':sid,'revision':saved['revision']});assert response.status_code==200,response.text
        run=wait(client,response.json()['id']);assert run['status']=='completed_with_errors'
        assert [i['status'] for i in run['items']]==['completed','completed','failed']
        assert 'SHA-256' in run['items'][2]['error']
        for source,out in zip(saved['items'],run['items'][:2]):
            assert out['analysis']==source['analysis']
            expected=client.post(f"/api/images/{out['image_id']}/analysis",headers=H,json=out['analysis']).json()
            assert {k:v for k,v in out['result'].items() if k not in ('report_id','created_utc')}=={k:v for k,v in expected.items() if k not in ('report_id','created_utc')}
        assert run['items'][0]['result']['results'][0]['pixel_count']!=run['items'][1]['result']['results'][0]['pixel_count']
        xlsx=client.get(f"/api/batch/runs/{run['id']}/xlsx",headers=H);assert xlsx.status_code==200,xlsx.text
        with ZipFile(io.BytesIO(xlsx.content)) as z:
            ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            sheet=ET.fromstring(z.read('xl/worksheets/sheet2.xml'))
            assert not sheet.findall('.//s:f',ns)
            condition=sheet.find(".//s:c[@r='H2']",ns);assert condition.attrib['t']=='inlineStr'
            assert condition.find('s:is/s:t',ns).text.startswith('=HYPERLINK')
            numeric=ET.fromstring(z.read('xl/worksheets/sheet5.xml')).find(".//s:c[@r='F2']/s:v",ns)
            assert int(numeric.text)==run['items'][0]['result']['results'][0]['pixel_count']
        draft['revision']=saved['revision'];draft['items'][0]['analysis']['rois'][0]['diameter_um']=4
        client.post('/api/batch/sessions/'+sid,headers=H,json=draft)
        assert client.get('/api/batch/runs/'+run['id'],headers=H).json()==run
        assert not (tmp_path/a['id']/'metadata.json').read_text().find('diameter_um')>=0
        assert client.get('/api/batch/runs/'+run['id']).status_code==401
    with TestClient(create_app(tmp_path,'token')) as client:
        assert client.get('/api/batch/sessions/'+sid,headers=H).json()['items'][0]['analysis']['rois'][0]['diameter_um']==4


def test_batch_calibration_changes_need_review_and_empty_drafts(tmp_path):
    with TestClient(create_app(tmp_path,'token')) as client:
        image=upload(client);entry=item(image);entry['analysis']['rois']=[]
        draft={'items':[entry]}
        saved=client.post('/api/batch/sessions',headers=H,json=draft).json()
        assert client.post('/api/batch/runs',headers=H,json={'session_id':saved['id'],'revision':1}).status_code==422
        entry['analysis']=item(image)['analysis'];draft['revision']=1
        saved=client.post('/api/batch/sessions/'+saved['id'],headers=H,json=draft).json()
        client.post('/api/images/'+image['id']+'/inspect',headers=H,json={'spacing_um':{'X':.3,'Y':.4,'Z':.6}})
        assert client.post('/api/batch/runs',headers=H,json={'session_id':saved['id'],'revision':2}).status_code==409
        draft['revision']=2
        revised=client.post('/api/batch/sessions/'+saved['id'],headers=H,json=draft).json()
        assert revised['items'][0]['reviewed'] is False


def test_cancel_then_interrupted_job_is_preserved(tmp_path,monkeypatch):
    import organelle_scope.batch as module
    entered=Event();release=Event()
    real=module.compute_analysis
    def slow(*args,**kwargs):
        entered.set();release.wait(3);args[-1]();return real(*args,**kwargs)
    monkeypatch.setattr(module,'compute_analysis',slow)
    with TestClient(create_app(tmp_path,'token')) as client:
        image=upload(client)
        saved=client.post('/api/batch/sessions',headers=H,json={'items':[item(image)]}).json()
        args={'session_id':saved['id'],'revision':1}
        run=client.post('/api/batch/runs',headers=H,json=args).json();assert entered.wait(3)
        assert client.post('/api/batch/runs',headers=H,json=args).status_code==409
        assert client.get(f"/api/batch/runs/{run['id']}/xlsx",headers=H).status_code==409
        client.post(f"/api/batch/runs/{run['id']}/cancel",headers=H);release.set()
        value=wait(client,run['id']);assert value['status']=='cancelled'
        assert value['items'][0]['status']=='cancelled'
    p=tmp_path/'batch-data'/'runs'/f"{run['id']}.json";value['status']='running';value['items'][0]['status']='running';p.write_text(json.dumps(value))
    with TestClient(create_app(tmp_path,'token')) as client:
        assert client.get('/api/batch/runs/'+run['id'],headers=H).json()['status']=='interrupted'


def test_excel_undefined_is_blank_and_strings_are_literal():
    with ZipFile(io.BytesIO(workbook([('Test',[['Name','Value'],['=1+1',None],['<test>',1.25]])]))) as z:
        ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        assert root.find(".//s:c[@r='B2']",ns) is None
        assert root.find(".//s:c[@r='A2']",ns).attrib['t']=='inlineStr'
        assert root.find(".//s:c[@r='B3']/s:v",ns).text=='1.25'
        assert not root.findall('.//s:f',ns)


def test_channel_correction_invalidates_batch_review_and_preserves_old_run_labels(tmp_path):
    with TestClient(create_app(tmp_path,'token')) as client:
        image=upload(client)
        first=client.post('/api/batch/sessions',headers=H,json={'items':[item(image)]}).json()
        run=client.post('/api/batch/runs',headers=H,json={'session_id':first['id'],'revision':1}).json()
        original=wait(client,run['id']);assert original['status']=='completed'
        assert original['design_review']['groups'][0]['labelled_experiments']==1
        info=image['info']
        changed=client.post('/api/images/'+image['id']+'/channels',headers=H,json={'labels':['Marker B','Marker A'],'expected_image_info':info})
        assert changed.status_code==200,changed.text
        assert client.post('/api/batch/runs',headers=H,json={'session_id':first['id'],'revision':1}).status_code==409
        revised=client.post('/api/batch/sessions/'+first['id'],headers=H,json={'revision':1,'items':[item(image)]}).json()
        assert not revised['items'][0]['reviewed']
        assert revised['items'][0]['image']['info']['channel_labels']==['Marker B','Marker A']
        assert revised['items'][0]['analysis']['rois']==first['items'][0]['analysis']['rois']
        assert client.get('/api/batch/runs/'+run['id'],headers=H).json()==original
        export=client.get('/api/batch/runs/'+run['id']+'/xlsx',headers=H)
        with ZipFile(io.BytesIO(export.content)) as book:
            assert b'Design review' in book.read('xl/workbook.xml')
