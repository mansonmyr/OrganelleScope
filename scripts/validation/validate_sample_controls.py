"""Owner-supplied sample controls: inspectable candidate ROIs, never fitted to an expected outcome.
No sample files, biological labels or resulting measurements are uploaded by this tool.
"""
import argparse,hashlib,json,tempfile
from pathlib import Path
from uuid import uuid4
import numpy as np,tifffile
from scipy import ndimage,stats
from skimage.feature import peak_local_max
from skimage.filters import threshold_otsu
from PIL import Image,ImageDraw
from fastapi.testclient import TestClient
from organelle_scope.image_io import inspect_tiff,read_plane
from organelle_scope.main import create_app

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path);parser.add_argument('--annotations',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True);annotations=json.loads(args.annotations.read_text(encoding='utf-8'))['files'];report={'protocol':'Reference-channel-only local maxima after one-pixel Gaussian smoothing for candidate selection; raw intensities for measurements. Up to five candidates, at least 2 µm apart (or 20 pixels if physical spacing unconfirmed). Predefined circle diameters 1, 2, 3 µm; 30 pixels if uncalibrated. Native single-plane ROIs; no projection-based correlation. Zero and whole-volume Otsu threshold sensitivity, no selection of a favourable setting.','scope':'Owner-supplied, non-blinded sample-control consistency analysis. Candidate regions require visual review. No pooled biological significance, independent-replicate claim, universal specificity estimate or direct-binding conclusion. Raw sources unchanged.','files':[]}
with tempfile.TemporaryDirectory(prefix='OrganelleScope-control-') as temporary,TestClient(create_app(Path(temporary),'controls')) as client:
 for filename,annotation in annotations.items():
  path=args.directory/filename
  with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
  if digest!=annotation['source_sha256']:raise ValueError('Source changed; reconfirm annotations.')
  info=inspect_tiff(path);d=info.dimensions;labels=[c['label'] for c in annotation['channels']];info.channel_labels=labels
  pair=sorted(c-1 for c in annotation['primary_pair_1based']);reference=annotation['reference_channel_1based']-1
  # Read only selected channels in their native Z order, avoiding a full multichannel duplicate.
  volumes={c:np.stack([read_plane(path,info,c,z) for z in range(d['Z'])]) for c in set(pair+[reference])}
  calibrated=annotation.get('physical_spacing_confirmed',True) and all(info.calibration[a].value_um is not None for a in 'XYZ')
  spacing=np.array([info.calibration[a].value_um or 1 for a in 'ZYX']) if calibrated else np.ones(3)
  smooth=ndimage.gaussian_filter(volumes[reference].astype('float32'),sigma=(0,1,1))
  candidates=peak_local_max(smooth,min_distance=3,threshold_abs=float(np.percentile(smooth,99.5)),exclude_border=False,num_peaks=100)
  selected=[]
  for z,y,x in candidates:
   if x<10 or y<10 or x>=d['X']-10 or y>=d['Y']-10:continue
   if all(np.linalg.norm((np.array([z,y,x])-p)*spacing)>=(2 if calibrated else 20) for p in selected):selected.append(np.array([z,y,x]))
   if len(selected)==5:break
  del smooth
  ident=str(uuid4());folder=Path(temporary)/ident;folder.mkdir();(folder/'source.tiff').symlink_to(path.resolve());(folder/'metadata.json').write_text(json.dumps({'id':ident,'sha256':digest,'info':info.model_dump(),'options':{},'import_schema':2}),encoding='utf-8')
  base='/api/images/'+ident;headers={'X-Session-Token':'controls'};thresholds=[0.]*d['C']
  for c in pair:thresholds[c]=float(threshold_otsu(volumes[c]))
  entries=[]
  for n,center in enumerate(selected):
   z,y,x=map(int,center)
   for diameter in ([1.,2.,3.] if calibrated else [30.]):
    radius_x=diameter/(2*spacing[2]) if calibrated else diameter/2
    roi={'id':f'candidate-{n+1}-diameter-{diameter}','kind':'circle','z':z,'points':[{'x':x,'y':y},{'x':x+radius_x,'y':y}]}
    for mode in ['zero','manual']:
     req={'rois':[roi],'target_channel':pair[0],'threshold_mode':mode,'thresholds':thresholds if mode=='manual' else []}
     response=client.post(base+'/analysis',headers=headers,json=req);response.raise_for_status();result=response.json()['results'][0]
     measured=next(p for p in result['pairs'] if [p['channel_a'],p['channel_b']]==pair)
     # Independent native-page sampling and SciPy coefficient cross-check.
     yy,xx=np.mgrid[:d['Y'],:d['X']];mask=((xx-x)*spacing[2])**2+((yy-y)*spacing[1])**2<=(diameter/2)**2 if calibrated else (xx-x)**2+(yy-y)**2<=(diameter/2)**2
     a=volumes[pair[0]][z][mask].astype(float);b=volumes[pair[1]][z][mask].astype(float)
     # The application's rasterizer uses pixel centers; retain counts and compare its returned mask separately below.
     from organelle_scope.roi_analysis import AreaROI,roi_mask
     engine_mask,_=roi_mask(AreaROI.model_validate(roi),(d['Y'],d['X']),(info.calibration['X'].value_um,info.calibration['Y'].value_um))
     a=volumes[pair[0]][z][engine_mask].astype(float);b=volumes[pair[1]][z][engine_mask].astype(float)
     if a.std()>0 and b.std()>0:
      assert np.isclose(measured['pcc'],stats.pearsonr(a,b).statistic,atol=1e-10)
      assert np.isclose(measured['spearman'],stats.spearmanr(a,b).statistic,atol=1e-10)
     entries.append({'candidate':n+1,'center_zyx':center.tolist(),'diameter':diameter,'diameter_unit':'µm' if calibrated else 'pixels','roi':roi,'threshold_mode':mode,'pair':measured,'pixel_count':result['pixel_count']})
  # Presentation only: independent per-channel percentile stretch clearly labelled.
  panels=[]
  for c in pair:
   projection=volumes[c].max(axis=0).astype(float);lo,hi=np.percentile(projection,[1,99.8]);gray=(np.clip((projection-lo)/max(hi-lo,1),0,1)*255).astype('uint8')
   panel=Image.fromarray(gray).convert('RGB');draw=ImageDraw.Draw(panel)
   for n,(z,y,x) in enumerate(selected):
    r=1/spacing[2] if calibrated else 15;draw.ellipse((x-r,y-r,x+r,y+r),outline='yellow',width=2);draw.text((x+r,y),str(n+1),fill='yellow')
   panel.thumbnail((650,650));panels.append(panel)
  canvas=Image.new('RGB',(sum(p.width for p in panels),max(p.height for p in panels)+65),'white');draw=ImageDraw.Draw(canvas);offset=0
  for c,panel in zip(pair,panels):canvas.paste(panel,(offset,45));draw.text((offset+5,5),labels[c],fill='black');offset+=panel.width
  draw.text((5,25),'Z maximum projection; contrast stretched for review only. Yellow = proposed ROI locations, not reviewed cells.',fill='black')
  image_name=f'control-review-{len(report["files"])+1}.png';canvas.save(args.output/image_name)
  report['files'].append({'filename':filename,'source_sha256':digest,'channel_labels':labels,'reference_channel_1based':reference+1,'primary_pair_1based':[c+1 for c in pair],'expected_context':annotation.get('intended_comparison'),'dimensions':d,'calibrated_roi_sizes':calibrated,'thresholds':thresholds,'proposed_candidates':len(selected),'roi_review_status':'pending visual review','review_image':image_name,'results':entries,'independent_coefficient_checks':'All defined Pearson/Spearman values agree with independent SciPy functions on the same sampled source pixels.'})
  with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==digest
  print(filename,':',len(selected),'proposed ROIs;',len(entries),'setting/size results',flush=True)
(args.output/'control-validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
