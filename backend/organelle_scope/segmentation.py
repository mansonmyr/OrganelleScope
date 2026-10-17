"""Inspectable threshold masks in a bounded source cuboid; no organelle classifier."""
import io,json
from pathlib import Path
import numpy as np
from scipy import ndimage
from fastapi import Depends,HTTPException
from fastapi.responses import Response
from pydantic import Field
from organelle_scope.volume_analysis import CuboidRequest
from organelle_scope.roi_analysis import AreaROI,roi_mask
from organelle_scope.processing import process_plane,provenance
from organelle_scope.image_io import ImageError,read_plane

class SegmentationRequest(CuboidRequest):
    channel:int=Field(default=0,ge=0,le=3)
    method:str=Field(default='otsu',pattern='^(otsu|manual)$')
    threshold:float=Field(default=0,ge=0,allow_inf_nan=False)
    min_voxels:int=Field(default=8,ge=1,le=500000)
    connectivity:int=Field(default=1,ge=1,le=3)
    compartment:str=Field(default='User-defined compartment',max_length=100)
    exclude_labels:list[int]=Field(default_factory=list,max_length=1000)
    add_rois:list[AreaROI]=Field(default_factory=list,max_length=100)
    remove_rois:list[AreaROI]=Field(default_factory=list,max_length=100)
    reference_channel:int|None=Field(default=None,ge=0,le=3)
    reference_threshold:float=Field(default=0,ge=0,allow_inf_nan=False)
    radial_bin_um:float|None=Field(default=None,gt=0,le=100,allow_inf_nan=False)
    radial_max_um:float=Field(default=5,gt=0,le=100,allow_inf_nan=False)
    radial_center_zyx:list[float]|None=Field(default=None,min_length=3,max_length=3)
    near_distance_um:float=Field(default=1,gt=0,le=1000,allow_inf_nan=False)


def segment_volume(volume,options,spacing):
    from skimage.filters import threshold_otsu
    from skimage.measure import marching_cubes
    threshold=float(threshold_otsu(volume)) if options.method=='otsu' and float(volume.max())>float(volume.min()) else (float(volume.max()) if options.method=='otsu' else options.threshold)
    mask=volume>threshold;edit_warnings=[]
    for rois,value in [(options.add_rois,True),(options.remove_rois,False)]:
        for roi in rois:
            if not options.z0<=roi.z<=options.z1:raise ImageError('Manual mask edits must lie within the selected cuboid Z range.')
            if options.z0<=roi.z<=options.z1:
                # Manual edits are recorded in full source XY coordinates.
                shifted=roi.model_copy(update={'points':[p.model_copy(update={'x':p.x-options.x0,'y':p.y-options.y0}) for p in roi.points]})
                edit,warnings=roi_mask(shifted,mask.shape[1:],(spacing[2],spacing[1]));edit_warnings.extend(warnings);mask[roi.z-options.z0][edit]=value
    labels,count=ndimage.label(mask,ndimage.generate_binary_structure(3,options.connectivity))
    counts=np.bincount(labels.ravel());keep=counts>=options.min_voxels;keep[0]=False
    for ident in options.exclude_labels:
        if ident<1 or ident>=len(keep):raise ImageError('An excluded object ID is not present in this segmentation. Review the current mask first.')
        keep[ident]=False
    labels=np.where(keep[labels],labels,0).astype(np.uint32);mask=labels>0
    physical=all(s is not None for s in spacing);scale=np.asarray(spacing if physical else [1.,1.,1.])
    objects=[]
    if np.count_nonzero(keep)>1000:raise ImageError('More than 1000 objects remain; refine threshold or minimum size before measuring.')
    for ident in np.flatnonzero(keep):
        coords=np.argwhere(labels==ident);centroid=coords.mean(axis=0)+[options.z0,options.y0,options.x0];eigen=np.linalg.eigvalsh(np.cov((coords*scale).T,bias=True)) if len(coords)>1 else np.zeros(3)
        objects.append({'label':int(ident),'voxel_count':len(coords),'volume_um3':float(len(coords)*scale.prod()) if physical else None,'centroid_zyx':centroid.tolist(),'centroid_zyx_um':(centroid*scale).tolist() if physical else None,'principal_rms_extents_um':np.sqrt(np.maximum(eigen,0)).tolist() if physical else None,'mean':float(volume[labels==ident].mean()),'sum':float(volume[labels==ident].sum(dtype=np.float64)),'touches_cuboid_edge':bool(np.any(coords.min(axis=0)==0) or np.any(coords.max(axis=0)==np.asarray(mask.shape)-1))})
    mesh=None
    if mask.any() and sum(mask.shape)>3:
        # Zero padding closes cut faces; flagged as cuboid boundaries, not real membranes.
        vertices,faces,_,_=marching_cubes(np.pad(mask.astype(np.float32),1),.5,spacing=tuple(scale))
        if len(vertices)<=50000 and len(faces)<=100000:
            vertices=vertices-scale+np.asarray([options.z0,options.y0,options.x0])*scale
            mesh={'vertices_xyz':vertices[:,::-1].tolist(),'faces':faces.tolist(),'units':'um' if physical else 'voxel','source_bounds':options.model_dump(include={'x0','x1','y0','y1','z0','z1'}),'boundary':'Cuboid cut faces are closed for display; this is a threshold surface, not a measured membrane.'}
    return labels,{'threshold':threshold,'edit_warnings':edit_warnings,'objects':objects,'foreground_voxels':int(mask.sum()),'object_count':len(objects),'mesh':mesh,'units':'um' if physical else 'voxel','connectivity_neighbors':{1:6,2:18,3:26}[options.connectivity]}


def register_segmentation(app,stored,authorized):
    def calculate(image_id,options):
        folder,record,info=stored(image_id);options.validate_bounds(info.dimensions);options.processing.validate_channels(info.dimensions['C'],info.bit_depth)
        if options.channel>=info.dimensions['C']:raise ImageError('Select an available marker channel.')
        spacing=[info.calibration[a].value_um for a in ['Z','Y','X']]
        volume=np.stack([process_plane(read_plane(folder/'source.tiff',info,options.channel,z),options.processing,options.channel,folder.parent,z)[options.y0:options.y1+1,options.x0:options.x1+1].copy() for z in range(options.z0,options.z1+1)])
        labels,result=segment_volume(volume,options,spacing)
        radial=None
        if options.radial_bin_um is not None:
            if not all(v is not None for v in spacing):raise ImageError('Radial enrichment requires known XYZ spacing.')
            if options.radial_max_um/options.radial_bin_um>200:raise ImageError('Choose at most 200 radial bins.')
            if options.radial_center_zyx is None and not labels.any():raise ImageError('Radial enrichment requires foreground or an explicit source-coordinate center.')
            center=np.asarray(options.radial_center_zyx if options.radial_center_zyx is not None else np.argwhere(labels>0).mean(axis=0)+[options.z0,options.y0,options.x0],dtype=float)
            if not np.isfinite(center).all():raise ImageError('Choose a finite radial center or a non-empty marker mask.')
            limits=np.asarray([info.dimensions[a] for a in ['Z','Y','X']])
            if np.any(center<0) or np.any(center>limits-1):raise ImageError('Radial center must be inside the source image.')
            positions=np.indices(labels.shape).transpose(1,2,3,0)+[options.z0,options.y0,options.x0]
            distances=np.linalg.norm((positions-center)*np.asarray(spacing),axis=-1)
            edges=np.arange(0,options.radial_max_um,options.radial_bin_um);edges=np.append(edges,options.radial_max_um)
            indices=np.searchsorted(edges,distances,side='right')-1
            radial={'center_source_zyx':center.tolist(),'bin_edges_um':edges.tolist(),'channels':[],'definition':'Mean intensity in spherical radial shells intersected with the selected cuboid; enrichment divides each shell mean by the whole-cuboid channel mean. Shell voxel counts and sampled volumes are reported; cut shells are not extrapolated. No radial pixels are independent biological replicates.'}
        for c in range(info.dimensions['C']):
            values=volume if c==options.channel else np.stack([process_plane(read_plane(folder/'source.tiff',info,c,z),options.processing,c,folder.parent,z)[options.y0:options.y1+1,options.x0:options.x1+1].copy() for z in range(options.z0,options.z1+1)])
            if radial is not None:
                whole=float(values.mean(dtype=np.float64));shells=[]
                for i in range(len(edges)-1):
                    selected=indices==i;count=int(selected.sum());mean=float(values[selected].mean(dtype=np.float64)) if count else None
                    shells.append({'inner_um':float(edges[i]),'outer_um':float(edges[i+1]),'voxel_count':count,'sampled_volume_um3':float(count*np.prod(spacing)),'mean':mean,'enrichment_over_cuboid_mean':mean/whole if count and whole>0 else None})
                radial['channels'].append({'channel':c,'label':info.channel_labels[c],'whole_cuboid_mean':whole,'shells':shells})
            totals=np.bincount(labels.ravel(),weights=values.ravel(),minlength=int(labels.max())+1)
            for obj in result['objects']:obj.setdefault('channel_intensities',[]).append({'channel':c,'label':info.channel_labels[c],'sum':float(totals[obj['label']]),'mean':float(totals[obj['label']]/obj['voxel_count'])})
        if radial is not None:result['radial_enrichment']=radial
        if options.reference_channel is not None:
            c=options.reference_channel
            if c>=info.dimensions['C'] or c==options.channel:raise ImageError('Select a different available reference channel.')
            reference=np.stack([process_plane(read_plane(folder/'source.tiff',info,c,z),options.processing,c,folder.parent,z)[options.y0:options.y1+1,options.x0:options.x1+1].copy() for z in range(options.z0,options.z1+1)])>options.reference_threshold
            if all(v is not None for v in spacing) and reference.any() and labels.any():
                distances=ndimage.distance_transform_edt(~reference,sampling=spacing)[labels>0]
                result['proximity']={'nearest_occupied_voxel_center_um':float(distances.min()),'median_occupied_voxel_center_um':float(np.median(distances)),'fraction_marker_voxels_within_distance':float(np.mean(distances<=options.near_distance_um)),'distance_threshold_um':options.near_distance_um,'definition':'Empirical fraction P(within threshold of reference foreground | selected marker foreground). Spatially dependent voxels; not a binding probability or a significance test. Registration and label offsets are unmeasured.'}
            else:result['proximity']={'unavailable_reason':'Both masks must contain foreground and XYZ calibration must be known.'}
        result.update(source_sha256=record['sha256'],image_id=image_id,image_info=record['info'],request=options.model_dump(),processing=provenance(options.processing,folder.parent),scope='Threshold-defined objects in the selected cuboid; user-named compartment, not automatic biological identification. Source resolution/registration limits apply.')
        return labels,result,volume
    @app.post('/api/images/{image_id}/segmentation',dependencies=[Depends(authorized)])
    def segment(image_id:str,options:SegmentationRequest):
        try:return calculate(image_id,options)[1]
        except (ImageError,ValueError,ImportError) as exc:raise HTTPException(422,str(exc)) from exc
    @app.post('/api/images/{image_id}/segmentation/preview',dependencies=[Depends(authorized)])
    def preview(image_id:str,options:SegmentationRequest,z:int=0):
        from PIL import Image
        try:
            labels,report,volume=calculate(image_id,options)
            if not options.z0<=z<=options.z1:raise ImageError('Choose a source Z slice within the cuboid.')
            index=z-options.z0;plane=volume[index];high=float(np.percentile(plane,99.5)) or 1
            rgb=np.repeat(np.clip(plane/high,0,1)[...,None],3,axis=2)
            edge=(labels[index]>0)&~ndimage.binary_erosion(labels[index]>0)
            rgb[edge]=[1,.49,0];image=Image.fromarray((rgb*255).astype(np.uint8));image.thumbnail((768,768));buf=io.BytesIO();image.save(buf,format='PNG');return Response(buf.getvalue(),media_type='image/png')
        except (ImageError,ValueError,ImportError) as exc:raise HTTPException(422,str(exc)) from exc
    @app.post('/api/images/{image_id}/segmentation/export',dependencies=[Depends(authorized)])
    def export(image_id:str,options:SegmentationRequest):
        import tifffile,zipfile
        try:
            labels,result,_=calculate(image_id,options);tiff=io.BytesIO();info=result['image_info'];spacing=[info['calibration'][a]['value_um'] for a in ['Z','Y','X']]
            metadata={'axes':'ZYX',**({f'PhysicalSize{a}':s for a,s in zip(['Z','Y','X'],spacing)} if all(s is not None for s in spacing) else {})}
            tifffile.imwrite(tiff,labels,ome=True,photometric='minisblack',metadata=metadata)
            result.pop('mesh',None);buf=io.BytesIO()
            with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as archive:archive.writestr('labels.ome.tif',tiff.getvalue());archive.writestr('measurement.json',json.dumps(result,allow_nan=False))
            return Response(buf.getvalue(),media_type='application/zip')
        except (ImageError,ValueError,ImportError) as exc:raise HTTPException(422,str(exc)) from exc
