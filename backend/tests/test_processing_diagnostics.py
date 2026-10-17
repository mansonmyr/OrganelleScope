import io
import numpy as np
import tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app

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

