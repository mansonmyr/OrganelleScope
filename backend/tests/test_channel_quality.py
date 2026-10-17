import hashlib
import io
import numpy as np
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app


def test_native_contrast_channel_annotation_identity_and_quality(tmp_path):
    raw=np.zeros((2,2,8,9),np.uint16);raw[0,0,0,:3]=[0,4095,65535];raw[0,1]=42
    buf=io.BytesIO();tifffile.imwrite(buf,raw,ome=True,photometric='minisblack',metadata={'axes':'ZCYX'})
    payload=buf.getvalue();h={'X-Session-Token':'t'}
    with TestClient(create_app(tmp_path/'images','t')) as client:
        image=client.post('/api/images',headers=h,files={'file':('synthetic.tif',payload)}).json();url='/api/images/'+image['id']
        assert client.get(url+'/quality').status_code==401
        quality=client.get(url+'/quality?z=0',headers=h).json()
        a,b=quality['channels'];assert a['storage_ceiling_pixels']==1 and a['zero_pixels']==70
        assert a['detector_saturation']=='not determined' and b['std']==0 and b['notes']
        assert client.get(url+'/quality?z=20',headers=h).status_code==422
        from PIL import Image
        native=np.array(Image.open(io.BytesIO(client.get(url+'/preview?luts=red,blue',headers=h).content)))
        assert native[0,1,0]==int(4095/65535*255) and native[0,2,0]==255
        auto=np.array(Image.open(io.BytesIO(client.get(url+'/preview?luts=red,blue&contrast=auto',headers=h).content)))
        assert auto[1,1,2]>native[1,1,2]  # constant nonzero B is only brightened on request
        assert client.get(url+'/preview?contrast=bogus',headers=h).status_code==422
        for names in [[],['A'],['A','A'],['','B'],['x'*121,'B'],['A\nB','C']]:
            assert client.post(url+'/channels',headers=h,json={'labels':names,'expected_image_info':image['info']}).status_code==422
        assert client.post(url+'/channels',headers=h,json={'labels':['Marker A','Marker B'],'expected_image_info':{}}).status_code==409
        roi={'id':'r','kind':'circle','z':0,'points':[{'x':4,'y':4},{'x':6,'y':4}]}
        options={'rois':[roi],'threshold_mode':'zero'}
        before=client.post(url+'/analysis',headers=h,json=options).json()
        original_report=(tmp_path/'images'/image['id']/'analysis.json').read_bytes()
        changed=client.post(url+'/channels',headers=h,json={'labels':[' Marker A ','Marker B'],'expected_image_info':image['info']}).json()
        assert changed['info']['channel_labels']==['Marker A','Marker B']
        assert changed['original_channel_labels']==image['info']['channel_labels']
        assert changed['sha256']==hashlib.sha256(payload).hexdigest()
        assert client.get(url+'/analysis',headers=h).status_code==409
        assert (tmp_path/'images'/image['id']/'analysis.json').read_bytes()==original_report
        after=client.post(url+'/analysis',headers=h,json=options).json()
        assert after['results'][0]['pairs'][0]['label_a']=='Marker A'
        for metric in ('pcc','spearman','thresholded_m1','thresholded_m2'):
            assert after['results'][0]['pairs'][0][metric]==before['results'][0]['pairs'][0][metric]
        calibrated=client.post(url+'/inspect',headers=h,json={'spacing_um':{'X':.1,'Y':.1,'Z':.2}}).json()
        assert calibrated['info']['channel_labels']==['Marker A','Marker B']
        assert (tmp_path/'images'/image['id']/'source.tiff').read_bytes()==payload
        np.testing.assert_array_equal(np.frombuffer(client.get(url+'/plane?channel=0&z=0',headers=h).content,'<u2').reshape(8,9),raw[0,0])
    with TestClient(create_app(tmp_path/'images','t')) as client:
        assert client.get(url,headers=h).json()['info']['channel_labels']==['Marker A','Marker B']
