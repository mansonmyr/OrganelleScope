"""Use the retained synthetic training model to audit structured noise and metric changes."""
import argparse,io,json,time
from pathlib import Path
import numpy as np,tifffile
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.roi_analysis import pair_metrics
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);args=p.parse_args()
reference=json.loads(Path('docs/N2V_SYNTHETIC_BENCHMARK.json').read_text());h={'X-Session-Token':'bias'};cases=[]
with TestClient(create_app(args.work,'bias')) as client:
    model=next(m for m in client.get('/api/restoration/models',headers=h).json() if m['weights_sha256']==reference['model_weights_sha256'])
    y,x=np.mgrid[:96,:96];truth=30+200*np.exp(-((x-45)**2+(y-45)**2)/100)+150*np.exp(-((x-65)**2+(y-25)**2)/20);other=np.roll(truth,5,axis=1);rng=np.random.default_rng(102017)
    for structured in (False,True):
        raw=[];predicted=[]
        for clean in (truth,other):
            values=rng.poisson(clean).astype(float)
            if structured:values+=15*np.sin(y*np.pi/4)
            values=np.maximum(values,0).astype(np.uint16);raw.append(values);b=io.BytesIO();tifffile.imwrite(b,values,ome=True,photometric='minisblack',metadata={'axes':'YX'})
            ident=client.post('/api/images',headers=h,files={'file':('synthetic-bias.tif',b.getvalue())}).json()['id'];job=client.post('/api/restoration/apply',headers=h,json={'model_id':model['id'],'image_id':ident,'confirm_model_match':True,'tile_size':64,'overlap':16}).json()
            for _ in range(600):
                result=client.get('/api/restoration/jobs/'+job['id'],headers=h).json()
                if result['status']=='complete':break
                if result['status'] in ('failed','cancelled'):raise RuntimeError(str(result))
                time.sleep(.1)
            assert result['status']=='complete'
            response=client.post('/api/images/'+ident+'/processing/plane',headers=h,json={'restoration_result_id':result['result_id']});assert response.status_code==200
            predicted.append(np.frombuffer(response.content,'<f4').reshape(96,96))
        pcc=lambda pair:float(np.corrcoef(pair[0].ravel(),pair[1].ravel())[0,1])
        cases.append({'noise':'Poisson plus shared sinusoidal row artifact' if structured else 'independent Poisson','truth_pearson':pcc([truth,other]),'raw_pearson':pcc(raw),'n2v_pearson':pcc(predicted),'raw_mse':float(np.mean((raw[0]-truth)**2)),'n2v_mse':float(np.mean((predicted[0]-truth)**2)),'sum_bias_percent':float(100*(predicted[0].sum(dtype=float)-truth.sum())/truth.sum())})
report={'model_weights_sha256':model['weights_sha256'],'cases':cases,'scope':'Two seeded synthetic conditions only. Structured noise is shared between channels and can inflate measured association. Better MSE is not proof of unbiased colocalization or molecular resolution. Model trained only on the independent Poisson fixtures in the separate benchmark.'}
Path('docs/RESTORATION_BIAS_BENCHMARK.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
