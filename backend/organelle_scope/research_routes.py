import io
import math
from datetime import datetime, timezone
from itertools import combinations
import numpy as np
from fastapi import Depends, HTTPException
from fastapi.responses import Response
from PIL import Image
from organelle_scope import __version__
from organelle_scope.display_luts import display_colors
from organelle_scope.image_io import ImageError, read_plane
from organelle_scope.processing import process_plane, provenance
from organelle_scope.roi_analysis import AnalysisRequest, analyze_roi
from organelle_scope.spatial_validation import SpatialRequest, spatial_shift, reference_benchmarks
from organelle_scope.volume_analysis import CuboidRequest, summarize_cuboid
from organelle_scope.sensitivity import RoiSweepRequest,scaled_roi


def register_research(app, stored, authorized):
    def stamp(record):
        return {'application_version':__version__,'source_sha256':record['sha256'],'image_info':record['info'],
                'created_utc':datetime.now(timezone.utc).isoformat()}

    @app.get('/api/validation/reference', dependencies=[Depends(authorized)])
    def reference():
        return reference_benchmarks()

    @app.post('/api/images/{image_id}/validation/sensitivity', dependencies=[Depends(authorized)])
    def sensitivity(image_id: str, options: AnalysisRequest):
        folder,record,info=stored(image_id)
        try:
            options.processing.validate_channels(info.dimensions['C'],info.bit_depth)
            if info.dimensions['C']<2 or options.target_channel>=info.dimensions['C']:
                raise ImageError('At least two channels and a valid regression target are required.')
            if len(options.rois)>20 or sum(info.dimensions[a] for a in 'XY')>20000:
                raise ImageError('Use at most 20 ROIs for sensitivity comparisons.')
            # Same thresholds for raw and processed data: isolate processing effects.
            thresholds=options.thresholds if options.threshold_mode=='manual' else [0.]*info.dimensions['C']
            if options.threshold_mode=='costes':
                raise ImageError('Choose manual or zero thresholds for a matched raw-versus-processed comparison.')
            if len(thresholds)!=info.dimensions['C'] or any(not math.isfinite(t) or t<0 or t>2**info.bit_depth-1 for t in thresholds):
                raise ImageError('Provide one finite threshold per channel within the source intensity range.')
            results=[]
            for z in sorted({r.z for r in options.rois}):
                raw=[read_plane(folder/'source.tiff',info,c,z) for c in range(info.dimensions['C'])]
                processed=[process_plane(a,options.processing,c,folder.parent,z) for c,a in enumerate(raw)]
                for roi in options.rois:
                    if roi.z!=z:continue
                    args=(roi,info.channel_labels,options.target_channel,options.threshold_mode,thresholds,(info.calibration['X'].value_um,info.calibration['Y'].value_um))
                    before=analyze_roi(raw,*args);after=analyze_roi(processed,*args)
                    changes=[]
                    for a,b in zip(before['pairs'],after['pairs']):
                        changes.append({'label_a':a['label_a'],'label_b':a['label_b'],**{key:None if a[key] is None or b[key] is None else b[key]-a[key] for key in ('pcc','spearman','moc','thresholded_m1','thresholded_m2')}})
                    results.append({'roi':roi.model_dump(),'raw':before,'processed':after,'deltas_processed_minus_raw':changes})
            return {**stamp(record),'processing':provenance(options.processing,folder.parent),'request':options.model_dump(),'results':results,
                    'reference_benchmarks':reference_benchmarks(),'scope':'Descriptive processing sensitivity; no biological confidence intervals or publication certification.'}
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc

    @app.post('/api/images/{image_id}/validation/parameter-sweep', dependencies=[Depends(authorized)])
    def parameter_sweep(image_id:str,options:RoiSweepRequest):
        folder,record,info=stored(image_id)
        try:
            if options.threshold_mode=='costes':raise ImageError('Choose explicit manual or zero thresholds for sensitivity sweeps.')
            if len(options.rois)>10 or info.dimensions['X']*info.dimensions['Y']*len({r.z for r in options.rois})*info.dimensions['C']>64_000_000:raise ImageError('Sweep budget: ten ROIs and 64 million source-plane values.')
            options.processing.validate_channels(info.dimensions['C'],info.bit_depth)
            if options.target_channel>=info.dimensions['C']:raise ImageError('Select an available target channel.')
            thresholds=options.thresholds if options.threshold_mode=='manual' else [0.]*info.dimensions['C']
            ceiling=2**info.bit_depth-1
            if len(thresholds)!=info.dimensions['C'] or any(not math.isfinite(t) or t<0 or t>ceiling for t in thresholds):raise ImageError('Provide valid thresholds for every channel.')
            if options.threshold_step>ceiling:raise ImageError('Threshold step exceeds the source storage range.')
            results=[]
            for z in sorted({r.z for r in options.rois}):
                planes=[process_plane(read_plane(folder/'source.tiff',info,c,z),options.processing,c,folder.parent,z) for c in range(info.dimensions['C'])]
                for roi in (r for r in options.rois if r.z==z):
                    variants=[('baseline',roi,thresholds),('size_smaller',scaled_roi(roi,1-options.size_fraction),thresholds),('size_larger',scaled_roi(roi,1+options.size_fraction),thresholds)]
                    for channel in range(info.dimensions['C']):
                        for sign in [-1,1]:
                            adjusted=list(thresholds);adjusted[channel]=max(0,min(ceiling,adjusted[channel]+sign*options.threshold_step))
                            variants.append((f'threshold_C{channel+1}_{"lower" if sign<0 else "higher"}',roi,adjusted))
                    rows=[]
                    for name,region,levels in variants:
                        try:
                            measured=analyze_roi(planes,region,info.channel_labels,options.target_channel,'manual',levels,(info.calibration['X'].value_um,info.calibration['Y'].value_um))
                            rows.append({'variant':name,'thresholds':levels,'result':measured})
                        except ImageError as exc:rows.append({'variant':name,'thresholds':levels,'unavailable_reason':str(exc)})
                    results.append({'roi_id':roi.id,'variants':rows})
            return {**stamp(record),'request':options.model_dump(),'results':results,'scope':'One factor at a time: size or one channel threshold. Polygon scaling uses the vertex-average centre; circles keep their centre and scale diameter/radius. Thresholds clip at storage bounds; repeated settings can result. Image-edge intersections are reported. These are descriptive settings sensitivity, not independent replicates, confidence intervals or an automatic best-setting selection.'}
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc

    @app.post('/api/images/{image_id}/validation/spatial', dependencies=[Depends(authorized)])
    def spatial(image_id: str, options: SpatialRequest):
        folder,record,info=stored(image_id)
        try:
            if not options.acknowledge_stationarity:
                raise ImageError('Confirm that whole-field translations are a defensible null model for this image before running the test.')
            if options.channel_a==options.channel_b:raise ImageError('Choose two different channels.')
            options.processing.validate_channels(info.dimensions['C'],info.bit_depth)
            channels=[process_plane(read_plane(folder/'source.tiff',info,c,options.roi.z),options.processing,c,folder.parent,options.roi.z) for c in (options.channel_a,options.channel_b)]
            return {**stamp(record),'request':options.model_dump(),'processing':provenance(options.processing,folder.parent),
                    **spatial_shift(*channels,options.roi,options.iterations,options.seed,(info.calibration['X'].value_um,info.calibration['Y'].value_um))}
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc

    @app.get('/api/images/{image_id}/orthogonal', dependencies=[Depends(authorized)])
    def orthogonal(image_id: str, axis: str='XY', x: int=0, y: int=0, z: int=0, channel: int=-1, luts: str | None=None):
        folder,_,info=stored(image_id)
        try:
            if axis not in ('XY','XZ','YZ') or any(v<0 or v>=info.dimensions[a] for a,v in zip('XYZ',(x,y,z))):
                raise ImageError('Choose a supported plane and coordinates inside the source volume.')
            if channel < -1 or channel>=info.dimensions['C']:raise ImageError('Invalid channel.')
            channels=range(info.dimensions['C']) if channel==-1 else [channel]
            colors=display_colors(luts,info.dimensions['C'])
            shape=(info.dimensions['Y'],info.dimensions['X']) if axis=='XY' else (info.dimensions['Z'],info.dimensions['X' if axis=='XZ' else 'Y'])
            output=np.zeros((*shape,3),np.float32)
            for c in channels:
                reference=read_plane(folder/'source.tiff',info,c,z)
                high=float(np.percentile(reference[::4,::4],99.5)) or float(reference.max()) or 1.
                if axis=='XY':data=reference
                else:
                    rows=[]
                    for k in range(info.dimensions['Z']):
                        plane=reference if k==z else read_plane(folder/'source.tiff',info,c,k)
                        rows.append(plane[y,:].copy() if axis=='XZ' else plane[:,x].copy())
                    data=np.stack(rows)
                output+=np.clip(data/high,0,1)[...,None]*colors[c]
            image=Image.fromarray((np.clip(output,0,1)*255).astype(np.uint8));image.thumbnail((1024,1024))
            buf=io.BytesIO();image.save(buf,format='PNG');return Response(buf.getvalue(),media_type='image/png')
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc

    @app.post('/api/images/{image_id}/cuboid', dependencies=[Depends(authorized)])
    def cuboid(image_id: str, options: CuboidRequest):
        folder,record,info=stored(image_id)
        try:
            if info.dimensions['Z']<2:raise ImageError('3D region measurements require a source stack with at least two planes.')
            options.validate_bounds(info.dimensions)
            options.processing.validate_channels(info.dimensions['C'],info.bit_depth)
            thresholds=options.thresholds or [0.]*info.dimensions['C']
            if len(thresholds)!=info.dimensions['C'] or any(not math.isfinite(t) or t<0 or t>2**info.bit_depth-1 for t in thresholds):
                raise ImageError('Provide one finite threshold per channel within the source intensity range.')
            values=[]
            for c in range(info.dimensions['C']):
                pieces=[]
                for z in range(options.z0,options.z1+1):
                    plane=read_plane(folder/'source.tiff',info,c,z)
                    if options.processing.active:plane=process_plane(plane,options.processing,c,folder.parent,z)
                    pieces.append(plane[options.y0:options.y1+1,options.x0:options.x1+1].ravel().copy())
                values.append(np.concatenate(pieces).astype(np.float64))
            return {**stamp(record),'algorithm_version':'cuboid-1','request':options.model_dump(),'processing':provenance(options.processing,folder.parent),
                    **summarize_cuboid(values,info.channel_labels,thresholds,[info.calibration[a].value_um for a in 'XYZ'])}
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc
