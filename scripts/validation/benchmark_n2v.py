"""Held-out synthetic Poisson benchmark; no clean targets enter training."""
import io,json,time,argparse
from pathlib import Path
import numpy as np,tifffile
from scipy.ndimage import gaussian_filter
from fastapi.testclient import TestClient
from organelle_scope.main import create_app

def main():
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();h={'X-Session-Token':'benchmark'};truths={};noisy={}
 with TestClient(create_app(args.work,'benchmark')) as client:
  ids=[]
  for seed in range(10):
   rng=np.random.default_rng(100+seed);y,x=np.mgrid[:96,:96];truth=np.full((96,96),30.)
   for width in [1.,2.,4.,8.,12.]:
    cx,cy=rng.uniform(15,81,2);truth+=rng.uniform(100,300)*np.exp(-((x-cx)**2+(y-cy)**2)/(2*width**2))
   data=rng.poisson(truth).astype(np.uint16);buf=io.BytesIO();tifffile.imwrite(buf,data,ome=True,photometric='minisblack',metadata={'axes':'YX'})
   record=client.post('/api/images',headers=h,files={'file':('synthetic-independent.tif',buf.getvalue())}).json();ids.append(record['id']);truths[record['id']]=truth;noisy[record['id']]=data
  def wait(response):
   assert response.status_code==200,response.text;job=response.json()
   for _ in range(6000):
    job=client.get('/api/restoration/jobs/'+job['id'],headers=h).json()
    if job['status'] in ['complete','failed','cancelled']:
     assert job['status']=='complete',job;return job
    time.sleep(.1)
   raise RuntimeError('Benchmark exceeded ten-minute budget')
  parameters={'name':'Synthetic benchmark only','train_ids':ids[:6],'validation_ids':[ids[6]],'epochs':10,'steps':50,'patch_size':32,'patches_per_image':64,'filters':16,'seed':1729}
  start=time.monotonic();trained=wait(client.post('/api/restoration/train',headers=h,json=parameters));training_seconds=time.monotonic()-start;results=[]
  for ident in ids[7:]:
   applied=wait(client.post('/api/restoration/apply',headers=h,json={'image_id':ident,'model_id':trained['model_id'],'tile_size':64,'overlap':16,'confirm_model_match':True}))
   response=client.post('/api/images/'+ident+'/processing/plane',headers=h,json={'restoration_result_id':applied['result_id']});assert response.status_code==200,response.text
   prediction=np.frombuffer(response.content,'<f4').reshape(96,96);truth=truths[ident];raw=noisy[ident]
   metrics=lambda a:{'mse':float(np.mean((a.astype(float)-truth)**2)),'sum_bias_percent':float(100*(a.sum(dtype=float)-truth.sum())/truth.sum()),'pearson_to_truth':float(np.corrcoef(a.ravel(),truth.ravel())[0,1])}
   results.append({'seed':100+ids.index(ident),'raw':metrics(raw),'n2v':metrics(prediction),'gaussian_sigma_1_reference':metrics(gaussian_filter(raw.astype(np.float32),1))})
  report={'implementation':'CAREamics 0.3.4, CPU, independent-channel 2D N2V, no batch normalization','parameters':parameters,'training_seconds':training_seconds,'model_bytes':trained['model_bytes'],'model_weights_sha256':next(m for m in client.get('/api/restoration/models',headers=h).json() if m['id']==trained['model_id'])['weights_sha256'],'validation_loss':trained.get('last_validation_loss'),'held_out_cases':results,'scope':'Synthetic independent Poisson noise, heterogeneous smooth structures and small puncta. Training seeds 100–105, validation 106, untouched test 107–109. Clean truth is used only for test scoring. Numerical efficacy under this simulation does not validate real acquisition noise, resolution, colocalization or biology.'}
  args.output.write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
