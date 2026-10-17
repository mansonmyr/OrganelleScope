"""Shared deterministic XY measurement path for interactive and batch analysis."""
import math
from organelle_scope.image_io import ImageError,read_plane
from organelle_scope.processing import process_plane,provenance
from organelle_scope.roi_analysis import analyze_roi


def compute_analysis(folder,record,info,options,checkpoint=lambda:None):
    count=info.dimensions['C']
    if count<2 or options.target_channel>=count:raise ImageError('Select an image with at least two channels and a valid target channel.')
    if len({r.id for r in options.rois})!=len(options.rois):raise ImageError('ROI identifiers must be unique.')
    thresholds=options.thresholds if options.threshold_mode=='manual' else [0.]*count
    if len(thresholds)!=count or any(not math.isfinite(t) or t<0 or t>2**info.bit_depth-1 for t in thresholds):raise ImageError('Provide one finite threshold per channel within the source intensity range.')
    options.processing.validate_channels(count,info.bit_depth)
    if options.processing.active and options.threshold_mode=='costes':raise ImageError('Automatic thresholds currently support raw integer intensities only. Select manual or zero thresholds for processed measurements.')
    results=[]
    for z in sorted({r.z for r in options.rois}):
        checkpoint();channels=[]
        for c in range(count):
            checkpoint();plane=read_plane(folder/'source.tiff',info,c,z)
            channels.append(process_plane(plane,options.processing,c,folder.parent,z) if options.processing.active else plane)
        for roi in options.rois:
            checkpoint()
            if roi.z==z:results.append(analyze_roi(channels,roi,info.channel_labels,options.target_channel,options.threshold_mode,thresholds,(info.calibration['X'].value_um,info.calibration['Y'].value_um)))
    return {'algorithm_version':'roi-3','processing':provenance(options.processing,folder.parent),'image_id':record['id'],'source_sha256':record['sha256'],'image_info':record['info'],
        'request':options.model_dump(),'results':results,'validation':{'status':'engineering-tested; biological validation pending','publication_ready':False,
        'limitations':['No spatially calibrated significance or experiment-level inference.','Independent microscopy-software and real-control benchmarks pending.'],'methods_document':'docs/ROI_STATISTICS.md'},
        'scope':f"Separate XY-plane ROIs; {'processed float32' if options.processing.active else 'native source'} intensities; no 3D or pooled biological inference."}
