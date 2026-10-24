"""Copyright (c) 2026 Kai Hong Ooi. SPDX-License-Identifier: GPL-3.0-only.

Python-only numerical runner using the application measurement routines.

Run python -m organelle_scope.cli --help from the extracted package.
TIFF input must use the ZCYX shape explicitly supplied in the sample manifest.
"""
import argparse, json, hashlib, sys
from pathlib import Path
import numpy as np
import tifffile
from .roi_analysis import AreaROI, roi_mask, pair_metrics
from .processing import ProcessingConfig, process_plane
from .proximity import proximity_summary

def calculate(data_dir, manifest, sample, mode):
    m=next(x for x in manifest if x['id']==sample)
    path=data_dir/m['filename']; digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=m['sha256']:raise ValueError('Image digest does not match sample manifest')
    a=tifffile.imread(path).reshape(m['shape'])
    mask,_=roi_mask(AreaROI.model_validate(m['roi']),a.shape[-2:],(m['spacing_um']['X'],m['spacing_um']['Y']))
    c,d=m['pair_zero_based'];z=m['roi']['z'];cfg=ProcessingConfig()
    ta,tb=(0,0) if mode=='zero' else (m['thresholds'][c],m['thresholds'][d])
    result=pair_metrics(process_plane(a[z,c],cfg,c)[mask],process_plane(a[z,d],cfg,d)[mask],mode,ta,tb)
    return {'sample':sample,'source_sha256':digest,'mode':mode,'roi':m['roi'],'selected_pixels':int(mask.sum()),'result':result}

def closed_form_demo():
    """Analytic expected values, independent of an alternative code implementation."""
    a=np.array([0,1,2,3],dtype=float)
    perfect=pair_metrics(a,2*a,'manual',1,2)
    negative=pair_metrics(a,3-a,'zero',0,0)
    marker=np.zeros((2,2,3),bool);reference=marker.copy()
    marker[0,0,0]=True;reference[1,0,2]=True
    distance=proximity_summary(marker,reference,[2.,1.,.5],2.)
    actual={'perfect_pearson':perfect['pcc'],'negative_pearson':negative['pcc'],
            'tied_spearman':pair_metrics(np.array([1,1,2,3]),np.array([1,1,2,3]),'zero')['spearman'],
            'manual_m1':perfect['thresholded_m1'],'manual_m2':perfect['thresholded_m2'],
            'anisotropic_distance_um':distance['marker_to_reference']['nearest_occupied_voxel_center_um']}
    expected={'perfect_pearson':1.,'negative_pearson':-1.,'tied_spearman':1.,
              'manual_m1':5/6,'manual_m2':5/6,'anisotropic_distance_um':5**.5}
    for key,value in expected.items():
        if not np.isclose(actual[key],value,rtol=0,atol=1e-12):
            raise AssertionError(f'{key}: {actual[key]} != {value}')
    return {'definition':'Closed-form identity and physical Pythagorean cases; no acquired images.',
            'actual':actual,'expected':expected,'absolute_tolerance':1e-12,'passed':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    d=sub.add_parser('demo',help='Replay a closed-form numerical reference table')
    d.add_argument('--output',type=Path,required=True)
    r=sub.add_parser('roi',help='Replay one manifest ROI')
    r.add_argument('--data',type=Path,required=True);r.add_argument('--sample',required=True)
    r.add_argument('--mode',choices=['zero','manual','costes'],default='manual')
    r.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('proximity',help='Calculate directed physical distances for two binary ZYX TIFFs')
    q.add_argument('--marker',type=Path,required=True);q.add_argument('--reference',type=Path,required=True)
    q.add_argument('--spacing',type=float,nargs=3,metavar=('Z','Y','X'),required=True)
    q.add_argument('--cutoff',type=float,required=True);q.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='demo':result=closed_form_demo()
    elif a.command=='roi':
        result=calculate(a.data,json.loads((a.data/'manifest.json').read_text()),a.sample,a.mode)
    else:
        marker=tifffile.imread(a.marker).astype(bool);reference=tifffile.imread(a.reference).astype(bool)
        result=proximity_summary(marker,reference,a.spacing,a.cutoff)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':main()
