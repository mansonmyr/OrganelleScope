"""Compare EDT summaries with exhaustive physical-coordinate nearest distances.
Small synthetic masks only; no biological validity or binding inference.
"""
import argparse,json
from pathlib import Path
import numpy as np
from organelle_scope.proximity import proximity_summary


def oracle(source,target,spacing):
    a=np.argwhere(source);b=np.argwhere(target)
    return np.sqrt((((a[:,None,:]-b[None,:,:])*spacing)**2).sum(axis=2)).min(axis=1)


def assess():
    rng=np.random.default_rng(20261018);results=[]
    for case in range(60):
        shape=(int(rng.integers(1,6)),int(rng.integers(2,8)),int(rng.integers(2,8)))
        a=rng.random(shape)<.2;b=rng.random(shape)<.25;a.flat[0]=True;b.flat[-1]=True
        spacing=np.asarray([1.7,.31,.12]) if case%2 else np.asarray([.2,.2,.2])
        cutoff=float(rng.choice([.12,.2,.31,.5,1.7]))
        report=proximity_summary(a,b,spacing,cutoff)
        for source,target,key in [(a,b,'marker_to_reference'),(b,a,'reference_to_marker')]:
            expected=oracle(source,target,spacing);actual=report[key]
            for metric,value in [('nearest_occupied_voxel_center_um',expected.min()),('median_occupied_voxel_center_um',np.median(expected)),('p95_occupied_voxel_center_um',np.percentile(expected,95))]:
                np.testing.assert_allclose(actual[metric],value,rtol=0,atol=1e-12)
            assert actual['within_distance_voxels']==int(np.count_nonzero(expected<=cutoff))
            assert actual['fraction_within_distance']==float(np.mean(expected<=cutoff))
        results.append({'case':case,'shape_zyx':shape,'spacing_zyx_um':spacing.tolist(),'threshold_um':cutoff,'both_directions_agree':True})
    return {'seed':20261018,'oracle':'Exhaustive pairwise distances in physical Z/Y/X coordinates; no EDT or nearest-neighbour library in oracle.','tolerance_um':1e-12,'cases':results,'scope':'Sixty synthetic geometries, both directions. Numerical verification only; no acquisition registration, organelle identity, binding or population accuracy established.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    report=assess();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print('60 bidirectional proximity cases agree with the independent oracle.')
