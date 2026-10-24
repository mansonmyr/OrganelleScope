"""Shared deterministic XY measurement path for interactive and batch analysis."""
import math
from datetime import datetime, timezone
from uuid import uuid4
import tifffile
from organelle_scope.image_io import ImageError,read_plane
from organelle_scope.processing import process_plane_with_background,provenance
from organelle_scope.roi_analysis import analyze_roi


def compute_analysis(folder,record,info,options,checkpoint=lambda:None, progress=lambda **values:None):
    count=info.dimensions['C']
    if count<2 or options.target_channel>=count:raise ImageError('Select an image with at least two channels and a valid target channel.')
    if len({r.id for r in options.rois})!=len(options.rois):raise ImageError('ROI identifiers must be unique.')
    thresholds=options.thresholds if options.threshold_mode=='manual' else [0.]*count
    if len(thresholds)!=count or any(not math.isfinite(t) or t<0 or t>2**info.bit_depth-1 for t in thresholds):raise ImageError('Provide one finite threshold per channel within the source intensity range.')
    options.processing.validate_channels(count,info.bit_depth)
    if options.processing.active and options.threshold_mode=='costes':raise ImageError('Automatic thresholds currently support raw integer intensities only. Select manual or zero thresholds for processed measurements.')
    results=[]
    planes=sorted({r.z for r in options.rois})
    total=len(planes)*count+len(options.rois);done=0
    # One TIFF directory parse per calculation. Retain only one Z plane's channels.
    with tifffile.TiffFile(folder/'source.tiff') as tf:
        for z in planes:
            checkpoint();channels=[];raw_channels=[];backgrounds=[]
            for c in range(count):
                checkpoint();progress(completed=done,total=total,stage='Reading channel',z=z,channel=c)
                plane=read_plane(folder/'source.tiff',info,c,z,tiff=tf)
                raw_channels.append(plane)
                if options.processing.active:
                    processed,background=process_plane_with_background(plane,options.processing,c,folder.parent,z)
                    channels.append(processed);backgrounds.append(background)
                else:channels.append(plane)
                done+=1
            for roi in options.rois:
                checkpoint()
                if roi.z==z:
                    progress(completed=done,total=total,stage='Measuring ROI',roi_id=roi.id,z=z)
                    results.append(analyze_roi(channels,roi,info.channel_labels,options.target_channel,options.threshold_mode,thresholds,(info.calibration['X'].value_um,info.calibration['Y'].value_um),raw_channels=raw_channels,backgrounds=backgrounds if backgrounds else None,intensity_ceiling=2**info.bit_depth-1))
                    done+=1
    checkpoint();progress(completed=total,total=total,stage='Complete')
    return {'algorithm_version':'roi-4-quality','report_id':str(uuid4()),'created_utc':datetime.now(timezone.utc).isoformat(),'processing':provenance(options.processing,folder.parent),'image_id':record['id'],'source_sha256':record['sha256'],'image_info':record['info'],
        'request':options.model_dump(),'results':results,'validation':{'status':'engineering-tested; biological validation pending','publication_ready':False,
        'limitations':['No spatially calibrated significance or experiment-level inference.','Independent microscopy-software and real-control benchmarks pending.'],'methods_document':'MANUAL.md#part-vi--roi-measurements-and-channel-associations'},
        'scope':f"Separate XY-plane ROIs; {'processed float32' if options.processing.active else 'native source'} intensities; no 3D or pooled biological inference."}


def save_analysis(folder,result):
    """Preserve the exact previous report before replacing the current-view pointer."""
    import hashlib,json
    history=folder/'analysis-history';history.mkdir(exist_ok=True)
    current=folder/'analysis.json'
    if current.exists():
        data=current.read_bytes();archived=history/(hashlib.sha256(data).hexdigest()+'.json')
        if not archived.exists():archived.write_bytes(data)
    data=json.dumps(result,allow_nan=False).encode();archived=history/(hashlib.sha256(data).hexdigest()+'.json')
    if not archived.exists():archived.write_bytes(data)
    temp=folder/('analysis-'+str(uuid4())+'.tmp');temp.write_bytes(data);temp.replace(current)
