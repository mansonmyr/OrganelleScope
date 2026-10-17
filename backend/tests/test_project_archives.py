import io,json,zipfile
import numpy as np
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app

def test_portable_project_and_separate_recovery_roundtrip(tmp_path):
    b=io.BytesIO();tifffile.imwrite(b,np.arange(60,dtype=np.uint16).reshape(3,4,5),ome=True,metadata={'axes':'ZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':.5},photometric='minisblack')
    h={'X-Session-Token':'test'}
    with TestClient(create_app(tmp_path/'one'/'images','test')) as c:
        im=c.post('/api/images',headers=h,files={'file':('s.tif',b.getvalue())}).json()
        body={'name':'Original','image_id':im['id'],'expected_image_info':im['info'],'state':{'core':{'z':2,'areas':[{'id':'r','kind':'circle','z':2,'points':[{'x':2,'y':2},{'x':3,'y':2}]}]},'workspaces':{}}}
        saved=c.post('/api/projects',headers=h,json=body).json()
        assert c.post('/api/recovery',headers=h,json={**body,'name':'Unsaved recovery'}).status_code==200
        assert len(c.get('/api/projects',headers=h).json())==1
        assert c.get('/api/recovery',headers=h).json()['name']=='Unsaved recovery'
        assert c.get('/api/projects/'+saved['id'],headers=h).json()['name']=='Original'
        exported=c.get('/api/projects/'+saved['id']+'/archive',headers=h);assert exported.status_code==200
    with TestClient(create_app(tmp_path/'two'/'images','test')) as c:
        imported=c.post('/api/project-archives/import',headers=h,files={'file':('project.zip',exported.content)})
        assert imported.status_code==200,imported.text
        result=imported.json();assert result['image']['id']!=im['id'] and result['image']['sha256']==im['sha256']
        assert result['state']==body['state'];assert c.get('/api/projects/'+result['id'],headers=h).status_code==200
        bad=io.BytesIO()
        with zipfile.ZipFile(bad,'w') as z:z.writestr('../escape',b'bad');z.writestr('project.json',json.dumps(saved))
        assert c.post('/api/project-archives/import',headers=h,files={'file':('bad.zip',bad.getvalue())}).status_code==422
        assert len(c.get('/api/images',headers=h).json())==1
        assert c.get('/api/recovery').status_code==401

def test_portable_project_preserves_verified_restoration_outputs(tmp_path):
    import time
    h={'X-Session-Token':'test'};b=io.BytesIO();a=np.arange(3*8*8,dtype=np.uint16).reshape(3,8,8)
    tifffile.imwrite(b,a,ome=True,photometric='minisblack',metadata={'axes':'ZYX','PhysicalSizeX':.1,'PhysicalSizeY':.1,'PhysicalSizeZ':.5})
    with TestClient(create_app(tmp_path/'a'/'images','test')) as c:
        im=c.post('/api/images',headers=h,files={'file':('a.tif',b.getvalue())}).json()
        job=c.post('/api/restoration/deconvolve',headers=h,json={'image_id':im['id'],'sigma_xy_um':.1,'sigma_z_um':.5,'iterations':2,'acknowledge_psf_model':True}).json()
        for _ in range(100):
            j=c.get('/api/restoration/jobs/'+job['id'],headers=h).json()
            if j['status']=='complete':break
            time.sleep(.05)
        assert j['status']=='complete'
        config={'restoration_result_id':j['result_id']}
        expected=c.post('/api/images/'+im['id']+'/processing/plane?z=1',headers=h,json=config).content
        saved=c.post('/api/projects',headers=h,json={'name':'Restored','image_id':im['id'],'expected_image_info':im['info'],'state':{'core':{'processing':config}}}).json()
        archive=c.get('/api/projects/'+saved['id']+'/archive',headers=h);assert archive.status_code==200
    with TestClient(create_app(tmp_path/'b'/'images','test')) as c:
        response=c.post('/api/project-archives/import',headers=h,files={'file':('restored.zip',archive.content)});assert response.status_code==200,response.text
        result=response.json();new=result['state']['core']['processing'];assert new['restoration_result_id']!=config['restoration_result_id']
        actual=c.post('/api/images/'+result['image']['id']+'/processing/plane?z=1',headers=h,json=new)
        assert actual.status_code==200,actual.text
        assert actual.content==expected
