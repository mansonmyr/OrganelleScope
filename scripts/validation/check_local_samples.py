"""Read-only sample QA against local files; results stay outside Git by default.

Example (use the project's backend Python environment):
  PYTHONPATH=backend python scripts/validation/check_local_samples.py "/path/to/samples"
TIFFs are registered with read-only symlinks in a disposable service store to
avoid duplicating large source files. This exercises stored-image analysis,
not the multipart upload/copy path or biological control validity.
"""
import argparse,hashlib,io,json,tempfile,time
from pathlib import Path
from uuid import uuid4
import numpy as np
import tifffile
from PIL import Image
from scipy.stats import pearsonr,spearmanr
from fastapi.testclient import TestClient
from organelle_scope.image_io import inspect_tiff,read_plane
from organelle_scope.main import create_app
from organelle_scope.roi_analysis import AreaROI,roi_mask

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('directory',type=Path)
parser.add_argument('--output',type=Path,default=Path('local-samples/local-sample-checks.json'))
args=parser.parse_args();paths=sorted(p for p in args.directory.iterdir() if p.suffix.lower() in {'.tif','.tiff'})
if not paths:raise SystemExit('No TIFF images found.')
report={'scope':'Technical stored-image checks only. Geometric-center test regions and arbitrary test recipes, not reviewed biological ROIs or validated processing choices. Channel-marker assignments are unconfirmed. No replicate/negative/positive interpretation. Upload copying is not exercised; large source files are read via temporary symlinks.','files':[]}
with tempfile.TemporaryDirectory(prefix='OrganelleScope-sample-check-') as scratch:
    root=Path(scratch);headers={'X-Session-Token':'sample-check'}
    with TestClient(create_app(root,'sample-check')) as client:
        for path in paths:
            started=time.perf_counter();before=hashlib.file_digest(path.open('rb'),'sha256').hexdigest();info=inspect_tiff(path);d=info.dimensions
            item={'filename':path.name,'source_sha256':before,'bytes':path.stat().st_size,'dimensions':d,'storage':info.dtype,'spacing_um':{a:info.calibration[a].value_um for a in 'XYZ'},'warnings':info.warnings,'channel_labels':info.channel_labels,'checks':[]}
            ident=str(uuid4());folder=root/ident;folder.mkdir();(folder/'source.tiff').symlink_to(path.resolve())
            record={'id':ident,'sha256':before,'info':info.model_dump(),'options':{},'import_schema':2};(folder/'metadata.json').write_text(json.dumps(record))
            base='/api/images/'+ident;z=d['Z']//2;native=[]
            with tifffile.TiffFile(path) as tf:
                # These samples use YX pages in C-fast ZCYX ImageJ ordering.
                assert info.source_axes in ('YX','ZCYX'),f'Review independent page mapping for {info.source_axes}'
                for zz in sorted({0,z,d['Z']-1}):
                    for c in range(d['C']):
                        expected=tf.pages[zz*d['C']+c].asarray();actual=read_plane(path,info,c,zz)
                        np.testing.assert_array_equal(actual,expected)
                        r=client.get(base+f'/plane?z={zz}&channel={c}',headers=headers);assert r.status_code==200
                        np.testing.assert_array_equal(np.frombuffer(r.content,'<u2').reshape(expected.shape),expected)
                        if zz==z:native.append(actual)
            item['checks'].append('first/middle/last Z and every channel: native plane API equals independently indexed TIFF pages')
            for palette in (None,','.join(['cyan']*d['C'])):
                response=client.get(base+f'/preview?z={z}'+('' if palette is None else '&luts='+palette),headers=headers);assert response.status_code==200
                preview=Image.open(io.BytesIO(response.content));assert max(preview.size)<=1024
            item['checks'].append('default and selected LUT PNG previews decode with bounded dimensions')
            recipe={'background':'rolling_ball','radius_px':3,'rolling_height':50,'sigma_px':.5,'offsets':[]}
            response=client.post(base+f'/processing/preview?z={z}',headers=headers,json=recipe);assert response.status_code==200,response.text
            Image.open(io.BytesIO(response.content)).verify();item['checks'].append('rolling-ball/Gaussian matched-contrast preview returns valid PNG (test settings, not optimized for biology)')
            roi={'id':'technical-center','kind':'circle','z':z,'points':[{'x':d['X']/2,'y':d['Y']/2},{'x':d['X']/2+15,'y':d['Y']/2}]}
            options={'rois':[roi],'target_channel':0,'threshold_mode':'zero','thresholds':[]}
            response=client.post(base+'/analysis',headers=headers,json=options)
            if d['C']==1:
                assert response.status_code==422;item['checks'].append('single-channel colocalization rejected explicitly');item['biological_colocalization']='not possible from one stored channel'
            else:
                assert response.status_code==200,response.text;analysis=response.json();mask,_=roi_mask(AreaROI.model_validate(roi),native[0].shape,(info.calibration['X'].value_um,info.calibration['Y'].value_um))
                pairs=analysis['results'][0]['pairs']
                for pair in pairs:
                    a=native[pair['channel_a']][mask].astype(float);b=native[pair['channel_b']][mask].astype(float)
                    if a.std()>0 and b.std()>0:
                        assert np.isclose(pair['pcc'],pearsonr(a,b).statistic,atol=1e-10)
                        assert np.isclose(pair['spearman'],spearmanr(a,b).statistic,atol=1e-10)
                item['checks'].append('all defined ROI Pearson/Spearman values match independent SciPy functions')
            if d['Z']>1:
                bounds={'x0':d['X']//2-32,'x1':d['X']//2+31,'y0':d['Y']//2-32,'y1':d['Y']//2+31,'z0':max(0,z-1),'z1':min(d['Z']-1,z+1)}
                response=client.post(base+'/cuboid',headers=headers,json=bounds);assert response.status_code==200,response.text;result=response.json();count=64*64*(bounds['z1']-bounds['z0']+1);assert result['voxel_count']==count
                with tifffile.TiffFile(path) as tf:
                    for c in range(d['C']):
                        total=sum(int(tf.pages[zz*d['C']+c].asarray()[bounds['y0']:bounds['y1']+1,bounds['x0']:bounds['x1']+1].sum(dtype=np.uint64)) for zz in range(bounds['z0'],bounds['z1']+1))
                        assert result['channels'][c]['sum']==total
                for axis in ('XY','XZ','YZ'):
                    r=client.get(base+f'/orthogonal?axis={axis}&x={d["X"]//2}&y={d["Y"]//2}&z={z}',headers=headers);assert r.status_code==200;Image.open(io.BytesIO(r.content)).verify()
                for c in range(d['C']):
                    r=client.get(base+f'/volume?channel={c}',headers=headers);assert r.status_code==200;shape=json.loads(r.headers['X-Volume-Shape']);assert len(r.content)==int(np.prod(shape))*2
                    assert max(shape)<=128
                item['checks'].append('inclusive XYZ cuboid counts/all-channel sums equal independent source-page crops; linked PNG sections and bounded volume payloads valid')
            else:
                assert client.get(base+'/volume',headers=headers).status_code==422;item['checks'].append('single-plane 3D volume rejected explicitly')
            after=hashlib.file_digest(path.open('rb'),'sha256').hexdigest();assert after==before;item['source_unchanged']=True;item['elapsed_seconds']=round(time.perf_counter()-started,3);report['files'].append(item)
            print(path.name+': '+str(len(item['checks']))+' checks passed',flush=True)
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print('Local report:',args.output)
