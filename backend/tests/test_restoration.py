import io,json,time,importlib.util
from pathlib import Path
from uuid import uuid4
import numpy as np
import pytest,tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.processing import ProcessingConfig,process_plane,provenance
from organelle_scope.restoration import plane_key,digest
from organelle_scope.image_io import ImageError

def test_verified_float_artifact_is_source_bound_and_has_provenance(tmp_path):
    raw=np.arange(30,dtype=np.uint16).reshape(5,6);ident=str(uuid4());root=tmp_path/'restoration-data'/'results'/ident;root.mkdir(parents=True);key=plane_key(raw,0)
    np.save(root/(key+'.npy'),raw.astype(np.float32)*.5)
    manifest={'source_sha256':'source','model':{'weights_sha256':'weights','careamics_version':'0.3.4','normalization':{'means':[1],'stds':[2]}},'inference':{'tile_size':64},'planes':{key:{'sha256':digest(root/(key+'.npy'))}}}
    (root/'manifest.json').write_text(json.dumps(manifest));config=ProcessingConfig(restoration_result_id=ident)
    np.testing.assert_array_equal(process_plane(raw,config,0,tmp_path),raw*.5)
    assert provenance(config,tmp_path)['denoising']['model_weights_sha256']=='weights'
    with pytest.raises(ImageError,match='does not cover'):process_plane(raw+1,config,0,tmp_path)
    np.save(root/(key+'.npy'),raw.astype(np.float32))
    with pytest.raises(ImageError,match='integrity'):process_plane(raw,config,0,tmp_path)

def test_restoration_validation_auth_and_tensor_only_import(tmp_path):
    with TestClient(create_app(tmp_path,'test')) as client:
        assert client.get('/api/restoration/status').status_code==401
        h={'X-Session-Token':'test'}
        assert client.post('/api/restoration/models/import',headers=h,files={'file':('unsafe.ckpt',b'not a model')}).status_code==422
        assert client.post('/api/restoration/train',headers=h,json={'train_ids':[],'validation_ids':[]}).status_code==422
        assert client.post('/api/images/invalid/processing/plane',headers=h,json={'restoration_result_id':'-'*36}).status_code==422

def test_processing_diagnostics_and_background_residual_views(tmp_path):
    raw=np.full((2,9,9),100,np.uint16);raw[:,4,4]=600;buf=io.BytesIO();tifffile.imwrite(buf,raw,ome=True,photometric='minisblack',metadata={'axes':'CYX'})
    from PIL import Image
    with TestClient(create_app(tmp_path,'test')) as client:
        h={'X-Session-Token':'test'};r=client.post('/api/images',headers=h,files={'file':('qc.tif',buf.getvalue())}).json();base='/api/images/'+r['id'];config={'background':'constant','offsets':[100,100]}
        report=client.post(base+'/processing/diagnostics',headers=h,json=config).json();row=report['channels'][0]
        assert row['raw_sum']==8600 and row['processed_sum']==500 and row['estimated_background_mean']==100
        assert row['changed_pixels']==81 and row['residual_rmse']==100
        assert row['residual_neighbor_correlation_x'] is None
        for view in ['background','residual']:
            response=client.post(base+'/processing/preview?view='+view,headers=h,json=config);assert response.status_code==200,response.text
            assert Image.open(io.BytesIO(response.content)).size==(9,9)
        assert client.post(base+'/processing/preview?view=fake',headers=h,json=config).status_code==422

@pytest.mark.skipif(importlib.util.find_spec('careamics') is None,reason='optional CAREamics runtime')
def test_real_n2v_training_safe_reload_tiling_and_measurement_delivery(tmp_path):
    h={'X-Session-Token':'test'}
    with TestClient(create_app(tmp_path,'test')) as client:
        ids=[]
        for seed in [12,13]:
            y,x=np.mgrid[:48,:48];clean=50+200*np.exp(-((x-23)**2+(y-24)**2)/50)
            raw=np.random.default_rng(seed).poisson(clean).astype(np.uint16)[None]
            b=io.BytesIO();tifffile.imwrite(b,raw,ome=True,photometric='minisblack',metadata={'axes':'CYX'})
            ids.append(client.post('/api/images',headers=h,files={'file':('synthetic.tif',b.getvalue())}).json()['id'])
        assert client.post('/api/restoration/train',headers=h,json={'train_ids':[ids[0]],'validation_ids':[ids[0]]}).status_code==422
        def wait(response):
            assert response.status_code==200,response.text
            ident=response.json()['id']
            for _ in range(1000):
                job=client.get('/api/restoration/jobs/'+ident,headers=h).json()
                if job['status'] in ('complete','failed','cancelled'):assert job['status']=='complete',job;return job
                time.sleep(.02)
            pytest.fail('Restoration job did not finish')
        trained=wait(client.post('/api/restoration/train',headers=h,json={'train_ids':ids[:1],'validation_ids':ids[1:],'epochs':1,'steps':1,'patch_size':32,'patches_per_image':8,'filters':8}))
        exported=client.get('/api/restoration/models/'+trained['model_id']+'/download',headers=h)
        imported=client.post('/api/restoration/models/import',headers=h,files={'file':('model.zip',exported.content)})
        assert imported.status_code==200,imported.text
        applied=wait(client.post('/api/restoration/apply',headers=h,json={'model_id':imported.json()['id'],'image_id':ids[1],'tile_size':64,'overlap':16,'confirm_model_match':True}))
        response=client.post('/api/images/'+ids[1]+'/processing/plane',headers=h,json={'restoration_result_id':applied['result_id']})
        assert response.status_code==200,response.text
        pixels=np.frombuffer(response.content,'<f4');assert pixels.shape==(48*48,) and np.isfinite(pixels).all()
        recipe=client.post('/api/images/'+ids[1]+'/processing/recipe',headers=h,json={'restoration_result_id':applied['result_id']}).json()
        assert recipe['denoising']['source_sha256'] and recipe['denoising']['normalization']['stds'][0]>0
        assert not (tmp_path/'restoration-data'/'jobs'/trained['id']/'work').exists()

def test_identical_xy_planes_keep_distinct_z_context(tmp_path):
    raw=np.zeros((4,5),np.uint16);ident=str(uuid4());root=tmp_path/'restoration-data'/'results'/ident;root.mkdir(parents=True);planes={}
    for z,value in [(0,1),(1,2)]:
        key=plane_key(raw,0,z);p=root/(key+'.npy');np.save(p,np.full(raw.shape,value,np.float32));planes[key]={'sha256':digest(p)}
    (root/'manifest.json').write_text(json.dumps({'planes':planes}));config=ProcessingConfig(restoration_result_id=ident)
    assert process_plane(raw,config,0,tmp_path,0).mean()==1
    assert process_plane(raw,config,0,tmp_path,1).mean()==2
