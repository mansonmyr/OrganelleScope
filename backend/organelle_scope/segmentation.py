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
from organelle_scope.proximity import proximity_summary

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


class SegmentationSweepRequest(SegmentationRequest):
    threshold_step:float=Field(default=10,gt=0,allow_inf_nan=False)
    boundary_step:int=Field(default=1,ge=1,le=10)


def segment_volume(volume,options,spacing,make_mesh=True):
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
    if make_mesh and mask.any() and sum(mask.shape)>3:
        # Zero padding closes cut faces; flagged as cuboid boundaries, not real membranes.
        vertices,faces,_,_=marching_cubes(np.pad(mask.astype(np.float32),1),.5,spacing=tuple(scale))
        if len(vertices)<=50000 and len(faces)<=100000:
            vertices=vertices-scale+np.asarray([options.z0,options.y0,options.x0])*scale
            mesh={'vertices_xyz':vertices[:,::-1].tolist(),'faces':faces.tolist(),'units':'um' if physical else 'voxel','source_bounds':options.model_dump(include={'x0','x1','y0','y1','z0','z1'}),'boundary':'Cuboid cut faces are closed for display; this is a threshold surface, not a measured membrane.'}
    return labels,{'threshold':threshold,'edit_warnings':edit_warnings,'objects':objects,'foreground_voxels':int(mask.sum()),'object_count':len(objects),'mesh':mesh,'units':'um' if physical else 'voxel','connectivity_neighbors':{1:6,2:18,3:26}[options.connectivity]}


def register_segmentation(app,stored,authorized):
    def calculate(image_id,options,make_mesh=True,source_windows=None):
        folder,record,info=stored(image_id);options.validate_bounds(info.dimensions);options.processing.validate_channels(info.dimensions['C'],info.bit_depth)
        if options.channel>=info.dimensions['C']:raise ImageError('Select an available marker channel.')
        spacing=[info.calibration[a].value_um for a in ['Z','Y','X']]
        def channel_values(channel):
            if source_windows is not None:
                (x0,y0),windows=source_windows
                return np.stack([windows[channel,z][options.y0-y0:options.y1-y0+1,options.x0-x0:options.x1-x0+1] for z in range(options.z0,options.z1+1)])
            return np.stack([process_plane(read_plane(folder/'source.tiff',info,channel,z),options.processing,channel,folder.parent,z)[options.y0:options.y1+1,options.x0:options.x1+1].copy() for z in range(options.z0,options.z1+1)])
        volume=channel_values(options.channel)
        labels,result=segment_volume(volume,options,spacing,make_mesh)
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
            values=volume if c==options.channel else channel_values(c)
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
            reference=channel_values(c)>options.reference_threshold
            if all(v is not None for v in spacing):
                result['proximity']=proximity_summary(labels>0,reference,spacing,options.near_distance_um)
                result['proximity'].update(marker_channel=options.channel,reference_channel=c,marker_label=info.channel_labels[options.channel],reference_label=info.channel_labels[c],marker_mask='Threshold, connected-size filtering, exclusions and manual edits applied.',reference_mask='Strictly above reference threshold; no connected-size filter or marker-mask edits applied.')
            else:result['proximity']={'unavailable_reason':'XYZ calibration must be known.'}

        result.update(source_sha256=record['sha256'],image_id=image_id,image_info=record['info'],request=options.model_dump(),processing=provenance(options.processing,folder.parent),scope='Threshold-defined objects in the selected cuboid; user-named compartment, not automatic biological identification. Source resolution/registration limits apply.')
        return labels,result,volume
    @app.post('/api/images/{image_id}/segmentation',dependencies=[Depends(authorized)])
    def segment(image_id:str,options:SegmentationRequest):
        try:return calculate(image_id,options)[1]
        except (ImageError,ValueError,ImportError) as exc:raise HTTPException(422,str(exc)) from exc
    @app.post('/api/images/{image_id}/segmentation/sensitivity',dependencies=[Depends(authorized)])
    def segmentation_sensitivity(image_id:str,options:SegmentationSweepRequest):
        try:
            _,record,info=stored(image_id)
            if options.method!='manual':raise ImageError('Select a manual marker threshold before a controlled sensitivity sweep.')
            ceiling=2**info.bit_depth-1
            if options.threshold_step>ceiling or options.threshold>ceiling or options.reference_threshold>ceiling:raise ImageError('Threshold settings exceed the source storage range.')
            base=SegmentationRequest.model_validate(options.model_dump(exclude={'threshold_step','boundary_step'}))
            base.validate_bounds(info.dimensions)
            if base.exclude_labels:raise ImageError('Restore excluded objects before sweeping; object IDs may change.')
            base=base.model_copy(update={'radial_bin_um':None})
            variants=[('baseline',base)]
            for field in ['threshold','reference_threshold']:
                if field=='reference_threshold' and options.reference_channel is None:continue
                for sign in [-1,1]:variants.append((field+('_lower' if sign<0 else '_higher'),base.model_copy(update={field:max(0,min(ceiling,getattr(base,field)+sign*options.threshold_step))})))
            for sign in [-1,1]:
                bounds={}
                for a in 'xyz':
                    bounds[a+'0']=max(0,getattr(base,a+'0')-sign*options.boundary_step)
                    bounds[a+'1']=min(info.dimensions[a.upper()]-1,getattr(base,a+'1')+sign*options.boundary_step)
                variants.append(('cuboid_smaller' if sign<0 else 'cuboid_larger',base.model_copy(update=bounds)))
            budget=sum(max(0,v.x1-v.x0+1)*max(0,v.y1-v.y0+1)*max(0,v.z1-v.z0+1) for _,v in variants)
            if budget>2_000_000:raise ImageError('Sensitivity sweep exceeds two million total cuboid voxels. Use a smaller baseline cuboid.')
            valid=[]
            for _,value in variants:
                try:value.validate_bounds(info.dimensions);valid.append(value)
                except ImageError:pass
            union={a+'0':min(getattr(v,a+'0') for v in valid) for a in 'xyz'}
            union.update({a+'1':max(getattr(v,a+'1') for v in valid) for a in 'xyz'})
            folder,_,_=stored(image_id);windows={}
            base.processing.validate_channels(info.dimensions['C'],info.bit_depth)
            for channel in range(info.dimensions['C']):
                for z in range(union['z0'],union['z1']+1):
                    plane=process_plane(read_plane(folder/'source.tiff',info,channel,z),base.processing,channel,folder.parent,z)
                    windows[channel,z]=plane[union['y0']:union['y1']+1,union['x0']:union['x1']+1].copy()
            rows=[]
            for name,value in variants:
                try:
                    value.validate_bounds(info.dimensions)
                    if value.exclude_labels:raise ImageError('Restore excluded objects before sweeping; object IDs can change with threshold or bounds.')
                    _,result,_=calculate(image_id,value,make_mesh=False,source_windows=((union['x0'],union['y0']),windows))
                    rows.append({'variant':name,'request':value.model_dump(),'foreground_voxels':result['foreground_voxels'],'object_count':result['object_count'],'edit_warnings':result['edit_warnings'],'proximity':result.get('proximity'),'scope':result['scope']})
                except (ImageError,ValueError) as exc:rows.append({'variant':name,'request':value.model_dump(),'unavailable_reason':str(exc)})
            return {'source_sha256':record['sha256'],'image_info':record['info'],'request':options.model_dump(),'variants':rows,'scope':'One-factor threshold or cuboid-boundary changes. Radial shells and display surfaces are not recomputed. Processed source windows are reused within this request. Object IDs/denominators may change. Boundary steps are source voxels and have axis-specific physical sizes. Clamped/repeated settings are recorded. Unavailable variants are retained. This is descriptive sensitivity, not a confidence interval or a search for a favourable result.'}
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc

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
