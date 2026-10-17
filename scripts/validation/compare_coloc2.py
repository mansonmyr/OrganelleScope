"""Run installed Coloc 2 classes headlessly on identical masked native arrays."""
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
import numpy as np
from organelle_scope.roi_analysis import pair_metrics

def main():
    p=argparse.ArgumentParser();p.add_argument('--fiji',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    plugin=args.fiji/'plugins/Colocalisation_Analysis-3.1.0.jar';classpath=f'{args.fiji}/jars/*:{args.fiji}/plugins/*'
    source=Path(__file__).with_name('ColocReference.java');results=[]
    with tempfile.TemporaryDirectory(prefix='organellescope-coloc-') as tmp:
        subprocess.run([str(args.java_home/'bin/javac'),'-cp',classpath,'-d',tmp,str(source)],check=True,capture_output=True)
        rng=np.random.default_rng(20261017)
        for bits in [8,16]:
            top=2**bits-1
            a=rng.integers(0,top+1,257).astype(float);b=rng.integers(0,top+1,257).astype(float);a[::5]=0;b[::7]=0
            for name,other in [('independent',b),('positive',np.minimum(top,2*a)),('negative',top-a)]:
                for masking in ['full','irregular']:
                    mask=np.ones(a.shape,bool) if masking=='full' else rng.random(a.shape)>.35
                    fixture=np.column_stack([a,other,mask.astype(int)]);file=Path(tmp)/'pixels.csv';np.savetxt(file,fixture,delimiter=',',header='a,b,mask',comments='',fmt='%.17g')
                    run=subprocess.run([str(args.java_home/'bin/java'),'-Djava.awt.headless=true','-cp',tmp+':'+classpath,'ColocReference',str(file)],check=True,capture_output=True,text=True)
                    reference=json.loads(run.stdout.strip().splitlines()[-1]);local=pair_metrics(a[mask],other[mask],'zero')
                    differences={k:abs(local[k]-reference[k]) for k in ['pcc','spearman','m1','m2']}
                    results.append({'case':f'{bits}-bit {name} {masking}','selected_pixels':int(mask.sum()),'fixture_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'coloc2':reference,'organellescope':{k:local[k] for k in differences},'absolute_differences':differences,'passed':all(v<1e-10 for v in differences.values())})
    report={'plugin':plugin.name,'plugin_sha256':hashlib.sha256(plugin.read_bytes()).hexdigest(),'seed':20261017,'metrics':['Pearson','Spearman with ties','zero-threshold Manders M1/M2'],'tolerance':1e-10,'cases':results,'passed':all(r['passed'] for r in results),'scope':'Same native arrays and exact masks. No equivalence claim for Costes threshold rounding/search, spatial randomization, biological validity or image acquisition.'}
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False));print(json.dumps({'passed':report['passed'],'cases':len(results),'max_difference':max(max(r['absolute_differences'].values()) for r in results)}))
if __name__=='__main__':main()
