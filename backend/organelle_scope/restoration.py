"""Local CAREamics N2V jobs; safe tensor-only bundles and immutable float results."""
from datetime import datetime,timezone
from hashlib import sha256
import importlib.util
import io,json,os,shutil,zipfile
from pathlib import Path
from threading import Event,RLock,Thread
from uuid import UUID,uuid4
import numpy as np
from fastapi import Depends,HTTPException,UploadFile,File
from fastapi.responses import Response
from pydantic import BaseModel,ConfigDict,Field
from organelle_scope.image_io import ImageError,read_plane

class Cancelled(Exception):pass

def utc():return datetime.now(timezone.utc).isoformat()
def digest(path):
    h=sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def plane_key(source,channel,z=None):return (f'{channel}-z{z}-' if z is not None else f'{channel}-')+sha256(np.ascontiguousarray(source).tobytes()).hexdigest()
def result_manifest(root,ident):
    UUID(ident);p=root/'restoration-data'/'results'/ident/'manifest.json'
    if not p.is_file():raise ImageError('Denoising result is missing. Restore its local artifact folder or select raw measurements.')
    return json.loads(p.read_text())
def restored_plane(root,ident,source,channel,z=None):
    manifest=result_manifest(root,ident);key=plane_key(source,channel,z);item=manifest['planes'].get(key)
    if item is None:
        key=plane_key(source,channel);item=manifest['planes'].get(key)
    if not item:raise ImageError('This denoising result does not cover the requested source plane/channel. Run denoising for this image first.')
    p=root/'restoration-data'/'results'/ident/(key+'.npy')
    if not p.is_file() or digest(p)!=item['sha256']:raise ImageError('Denoised plane integrity check failed.')
    values=np.load(p,allow_pickle=False)
    if values.shape!=source.shape or values.dtype!=np.float32 or not np.isfinite(values).all():raise ImageError('Invalid denoised plane.')
    return values.copy()

class TrainOptions(BaseModel):
    model_config=ConfigDict(extra='forbid')
    model_config=ConfigDict(extra='forbid')
    name:str=Field(default='Local Noise2Void',min_length=1,max_length=120)
    train_ids:list[str]=Field(min_length=1,max_length=10)
    validation_ids:list[str]=Field(min_length=1,max_length=10)
    epochs:int=Field(default=10,ge=1,le=200)
    steps:int=Field(default=50,ge=1,le=500)
    patch_size:int=Field(default=64,ge=32,le=256,multiple_of=4)
    patches_per_image:int=Field(default=64,ge=8,le=256)
    filters:int=Field(default=32,ge=8,le=32,multiple_of=8)
    seed:int=Field(default=1729,ge=0,le=2**32-1)
    use_n2v2:bool=False
class ApplyOptions(BaseModel):
    model_config=ConfigDict(extra='forbid')
    model_id:str
    image_id:str
    tile_size:int=Field(default=256,ge=64,le=1024,multiple_of=4)
    overlap:int=Field(default=48,ge=8,le=128,multiple_of=4)
    confirm_model_match:bool=False

def factory(parameters,means,stds,channels):
    from careamics.config import create_advanced_n2v_config
    return create_advanced_n2v_config(experiment_name='OrganelleScope_N2V',data_type='array',axes='SCYX',
        patch_size=[parameters.patch_size]*2,batch_size=4,num_epochs=parameters.epochs,num_steps=parameters.steps,
        n_channels=channels,n_val_patches=8,num_workers=0,seed=parameters.seed,use_n2v2=parameters.use_n2v2,
        independent_channels=True,normalization='mean_std',normalization_params={'input_means':means,'input_stds':stds},
        model_params={'depth':2,'num_channels_init':parameters.filters,'use_batch_norm':False},
        trainer_params={'accelerator':'cpu','devices':1,'enable_model_summary':False,'num_sanity_val_steps':0,'log_every_n_steps':1},logger='none')

def load_engine(folder,work,callbacks):
    from careamics import CAREamist
    import torch
    manifest=json.loads((folder/'manifest.json').read_text())
    if digest(folder/'weights.npz')!=manifest['weights_sha256']:raise ImageError('Model tensor checksum mismatch.')
    parameters=TrainOptions.model_validate(manifest['parameters'])
    c=manifest['channels'];means=manifest['normalization']['means'];stds=manifest['normalization']['stds']
    if not 1<=c<=4 or len(means)!=c or len(stds)!=c or not np.isfinite(means+stds).all() or min(stds)<=0:raise ImageError('Invalid model normalization.')
    engine=CAREamist(factory(parameters,means,stds,c),work_dir=work,callbacks=callbacks,enable_progress_bar=False)
    with np.load(folder/'weights.npz',allow_pickle=False) as arrays:
        state={name:torch.from_numpy(arrays[name].copy()) for name in arrays.files}
    engine.model.n2v_manipulate.rng=torch.Generator(device='cpu').manual_seed(parameters.seed)
    engine.model.load_state_dict(state,strict=True)
    # CAREamics predicts from an explicit Lightning checkpoint. Generate it only
    # from this validated tensor-only state; uploaded pickle checkpoints are never loaded.
    import lightning
    engine.work_dir.mkdir(parents=True,exist_ok=True)
    checkpoint=engine.work_dir/'verified.ckpt'
    torch.save({'state_dict':engine.model.state_dict(),'pytorch-lightning_version':lightning.__version__,'epoch':0,'global_step':0},checkpoint)
    return engine,manifest

def register_restoration(app,data_dir,stored,authorized):
    root=data_dir/'restoration-data';lock=RLock();active={}
    def path(kind,ident):
        try:UUID(ident)
        except ValueError:raise HTTPException(404,'Restoration record not found.')
        return root/kind/ident
    def save_json(p,v):
        p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,allow_nan=False));tmp.replace(p)
    for file in (root/'jobs').glob('*/job.json'):
        record=json.loads(file.read_text())
        if record['status'] in ('running','pending','cancelling'):record.update(status='interrupted',finished=utc());save_json(file,record)
    def get_job(ident):
        p=path('jobs',ident)/'job.json'
        if not p.is_file():raise HTTPException(404,'Restoration job not found.')
        return json.loads(p.read_text())
    def model(ident):
        folder=path('models',ident)
        if not (folder/'manifest.json').is_file():raise HTTPException(404,'Noise2Void model not found.')
        return folder,json.loads((folder/'manifest.json').read_text())
    def runtime():
        if importlib.util.find_spec('careamics') is None:raise ImageError('The CAREamics runtime is not installed in this build. Install the restoration extra or use the full installer.')
        os.environ.setdefault('MPLCONFIGDIR',str(root/'runtime'/'matplotlib'))
        os.environ.setdefault('XDG_CACHE_HOME',str(root/'runtime'/'cache'))
        import torch
        torch.set_num_threads(min(4,os.cpu_count() or 1))
    def start(kind,options,work,needs_n2v=True):
        with lock:
            if active:raise HTTPException(409,'A restoration job is already active. Finish or cancel it first.')
            ident=str(uuid4());event=Event();record={'id':ident,'kind':kind,'status':'pending','created':utc(),'progress':0,'message':'Queued','request':options.model_dump()};active[ident]=event
            folder=path('jobs',ident);save_json(folder/'job.json',record)
        def update(**values):
            with lock:record.update(values);save_json(folder/'job.json',record)
        def checkpoint():
            if event.is_set():raise Cancelled()
        def worker():
            try:
                update(status='running',message='Loading local restoration runtime');
                if needs_n2v:runtime()
                checkpoint();work(ident,folder,checkpoint,update);checkpoint();update(status='complete',progress=1.,finished=utc(),message='Complete')
            except Cancelled:update(status='cancelled',finished=utc(),message='Cancelled; original TIFF unchanged')
            except Exception as exc:
                import traceback
                traceback.print_exc()
                update(status='failed',finished=utc(),message=str(exc))
            finally:
                # Work/checkpoints duplicate the verified tensor bundle; no research inputs are removed.
                shutil.rmtree(folder/'work',ignore_errors=True)
                if record['status'] in ('failed','cancelled'):
                    shutil.rmtree(root/'results'/ident,ignore_errors=True)
                    if kind=='train':shutil.rmtree(root/'models'/ident,ignore_errors=True)
                with lock:active.pop(ident,None)
        Thread(target=worker,daemon=True).start();return record.copy()
    def callback(checkpoint,update,epochs):
        from lightning.pytorch.callbacks import Callback
        class Progress(Callback):
            def on_train_batch_end(self,trainer,*args):checkpoint();update(message=f'Training epoch {trainer.current_epoch+1} of {epochs}',progress=min(.95,(trainer.current_epoch+min(1,(trainer.global_step%max(1,trainer.num_training_batches))/max(1,trainer.num_training_batches)))/epochs))
            def on_validation_epoch_end(self,trainer,*args):
                checkpoint();loss=trainer.callback_metrics.get('val_loss');update(last_validation_loss=float(loss) if loss is not None and np.isfinite(float(loss)) else None)
            def on_predict_batch_end(self,*args):checkpoint()
        return Progress()
    def source_snapshot(ident):
        folder,record,info=stored(ident)
        if info.needs_axis_confirmation or info.dimensions['T']!=1:raise ImageError('Confirm source axes and select a static image first.')
        return folder,record,info
    @app.get('/api/restoration/status',dependencies=[Depends(authorized)])
    def status():return {'available':importlib.util.find_spec('careamics') is not None,'implementation':'CAREamics 0.3.4 Noise2Void','device':'CPU, bounded to four threads','active_jobs':list(active),'training_scope':'independent-channel 2D UNet; Z planes are samples, not a 3D network'}
    @app.get('/api/restoration/models',dependencies=[Depends(authorized)])
    def models():return [json.loads(p.read_text()) for p in (root/'models').glob('*/manifest.json')]
    @app.get('/api/restoration/jobs',dependencies=[Depends(authorized)])
    def jobs():return sorted([json.loads(p.read_text()) for p in (root/'jobs').glob('*/job.json')],key=lambda r:r['created'],reverse=True)[:50]
    @app.get('/api/restoration/jobs/{ident}',dependencies=[Depends(authorized)])
    def job(ident:str):return get_job(ident)
    @app.post('/api/restoration/jobs/{ident}/cancel',dependencies=[Depends(authorized)])
    def cancel(ident:str):
        with lock:
            record=get_job(ident)
            if ident in active:active[ident].set();record.update(status='cancelling');save_json(path('jobs',ident)/'job.json',record)
            return record
    @app.post('/api/restoration/train',dependencies=[Depends(authorized)])
    def train(options:TrainOptions):
        try:
            entries={ident:source_snapshot(ident) for ident in set(options.train_ids+options.validation_ids)}
            hashes=lambda ids:{entries[i][1]['sha256'] for i in ids}
            if hashes(options.train_ids)&hashes(options.validation_ids):raise ImageError('Training and validation must use different source images, with different source checksums.')
            first=entries[options.train_ids[0]][2];channels=first.dimensions['C']
            if any(info.dimensions['C']!=channels or info.bit_depth!=first.bit_depth for _,_,info in entries.values()):raise ImageError('Training and validation images must have matching channel counts and bit depth.')
            if len(entries)*options.patches_per_image*channels*options.patch_size**2*4>512*1024**2:raise ImageError('Training patches exceed the 512 MiB budget. Reduce patch size/count or image count.')
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc
        def work(ident,folder,checkpoint,update):
            import torch
            from careamics import CAREamist
            rng=np.random.default_rng(options.seed);sampling={}
            def patches(ids):
                all_patches=[]
                for image_id in ids:
                    source,record,info=entries[image_id]
                    if digest(source/'source.tiff')!=record['sha256']:raise ImageError('Training source checksum changed.')
                    d=info.dimensions;p=options.patch_size
                    if min(d['X'],d['Y'])<p:raise ImageError('Training patch is larger than the source XY dimensions.')
                    coordinates=[]
                    for _ in range(options.patches_per_image):
                        checkpoint();z=int(rng.integers(d['Z']));y=int(rng.integers(d['Y']-p+1));x=int(rng.integers(d['X']-p+1));coordinates.append([z,y,x])
                        all_patches.append(np.stack([read_plane(source/'source.tiff',info,c,z)[y:y+p,x:x+p] for c in range(channels)]).astype(np.float32))
                    sampling[image_id]=coordinates
                return np.stack(all_patches)
            update(message='Sampling recorded patches from separate training/validation images')
            training=patches(options.train_ids);validation=patches(options.validation_ids)
            means=training.mean(axis=(0,2,3),dtype=np.float64).tolist();stds=training.std(axis=(0,2,3),dtype=np.float64).tolist()
            if min(stds)<=0:raise ImageError('A training channel is constant. Use independent raw acquisition channels with signal/noise variation.')
            torch.manual_seed(options.seed)
            engine=CAREamist(factory(options,means,stds,channels),work_dir=folder/'work',callbacks=[callback(checkpoint,update,options.epochs)],enable_progress_bar=False)
            # CAREamics 0.3.4 auto-selects the masking RNG device independently
            # from Lightning's accelerator. Keep it on the declared CPU baseline.
            engine.model.n2v_manipulate.rng=torch.Generator(device='cpu').manual_seed(options.seed)
            engine.train(train_data=training,val_data=validation);checkpoint()
            target=root/'models'/ident;target.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(target/'weights.npz',**{k:v.detach().cpu().numpy() for k,v in engine.model.state_dict().items()})
            manifest={'schema':'organelle-n2v-1','id':ident,'name':options.name,'created':utc(),'careamics_version':'0.3.4','channels':channels,'bit_depth':first.bit_depth,'channel_labels':first.channel_labels,'normalization':{'means':means,'stds':stds,'units':'native source intensities'},'parameters':options.model_dump(),'weights_sha256':digest(target/'weights.npz'),'sampling_zyx':sampling,'sources':{i:{'sha256':r['sha256'],'image_info':r['info'],'role':'training' if i in options.train_ids else 'validation'} for i,(_,r,_) in entries.items()},'validation':'Masked held-out-image loss is an engineering diagnostic, not clean ground truth or biological validation.'}
            save_json(target/'manifest.json',manifest)
            # Verify a tensor-only reload and exact state agreement before discarding checkpoints.
            reloaded,_=load_engine(target,folder/'work'/'reload',[])
            for k,v in engine.model.state_dict().items():torch.testing.assert_close(v.cpu(),reloaded.model.state_dict()[k].cpu(),rtol=0,atol=0)
            update(model_id=ident,model_bytes=(target/'weights.npz').stat().st_size)
        return start('train',options,work)
    @app.post('/api/restoration/apply',dependencies=[Depends(authorized)])
    def apply(options:ApplyOptions):
        mf,manifest=model(options.model_id)
        try:
            source,record,info=source_snapshot(options.image_id);d=info.dimensions
            if not options.confirm_model_match:raise ImageError('Review whether model training channels, acquisition and noise match this image, then confirm model compatibility.')
            if options.overlap>=options.tile_size:raise ImageError('Tile overlap must be smaller than the tile size.')
            if d['C']!=manifest['channels'] or info.bit_depth!=manifest['bit_depth']:raise ImageError('Model channel count or bit depth differs from this image.')
            if d['C']*d['Z']*d['X']*d['Y']*4>4*1024**3:raise ImageError('The float32 denoising result exceeds the current 4 GiB disk budget.')
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc
        def work(ident,folder,checkpoint,update):
            if digest(source/'source.tiff')!=record['sha256']:raise ImageError('Source checksum changed.')
            engine,model_manifest=load_engine(mf,folder/'work',[callback(checkpoint,update,1)])
            target=root/'results'/ident;target.mkdir(parents=True,exist_ok=True);planes={}
            for z in range(d['Z']):
                checkpoint();update(progress=z/d['Z'],message=f'Denoising source slice {z+1} of {d["Z"]}')
                raw=[read_plane(source/'source.tiff',info,c,z) for c in range(d['C'])]
                predictions,_=engine.predict(np.stack(raw)[None].astype(np.float32),axes='SCYX',tile_size=(options.tile_size,)*2,tile_overlap=(options.overlap,)*2,num_workers=0,batch_size=1,checkpoint=engine.work_dir/'verified.ckpt')
                output=np.asarray(predictions[0]).reshape((1,d['C'],d['Y'],d['X']))[0]
                if not np.isfinite(output).all():raise ImageError('Model prediction contains non-finite values.')
                for c,array in enumerate(output):
                    checkpoint();key=plane_key(raw[c],c,z);p=target/(key+'.npy');np.save(p,array.astype(np.float32),allow_pickle=False);planes[key]={'z_indices':planes.get(key,{}).get('z_indices',[])+[z],'channel':c,'sha256':digest(p)}
            checkpoint();save_json(target/'manifest.json',{'schema':'organelle-restored-1','id':ident,'source_sha256':record['sha256'],'image_id':record['id'],'image_info':record['info'],'model':model_manifest,'inference':options.model_dump(),'planes':planes,'created':utc(),'order':'Noise2Void on raw native intensities, inverse training normalization; further background/clipping/smoothing only when selected in the preparation recipe.'});update(result_id=ident)
        return start('apply',options,work)
    from organelle_scope.deconvolution import DeconvolutionOptions,gaussian_psf,richardson_lucy_reflect
    @app.post('/api/restoration/deconvolve',dependencies=[Depends(authorized)])
    def deconvolve(options:DeconvolutionOptions):
        try:
            source,record,info=source_snapshot(options.image_id);d=info.dimensions;axes=['Z','Y','X'] if d['Z']>1 else ['Y','X'];spacing=[info.calibration[a].value_um for a in axes]
            if not options.acknowledge_psf_model:raise ImageError('Review and acknowledge the PSF/noise model before deconvolution.')
            if d['Z']*d['Y']*d['X']*4>512*1024**2:raise ImageError('A channel volume exceeds the current 512 MiB deconvolution input budget.')
            if options.psf_image_id:
                pf,pr,pi=source_snapshot(options.psf_image_id)
                if pi.dimensions['C']!=1 or ((d['Z']>1)!=(pi.dimensions['Z']>1)):raise ImageError('Select a single-channel PSF with matching dimensionality.')
                if any(pi.dimensions[a]>129 or pi.dimensions[a]%2==0 for a in axes):raise ImageError('Measured PSF axes must be odd-sized and at most 129 voxels.')
                if any(s is None or pi.calibration[a].value_um is None or not np.isclose(s,pi.calibration[a].value_um,rtol=.01) for a,s in zip(axes,spacing)):raise ImageError('Measured PSF and source voxel spacing must be known and match within 1%; PSF resampling is not implicit.')
                kernel=np.stack([read_plane(pf/'source.tiff',pi,0,z) for z in range(pi.dimensions['Z'])]).astype(np.float32)
                if d['Z']==1:kernel=kernel[0]
                kernel=np.maximum(kernel-options.psf_background,0);psf_record={'kind':'measured image','source_sha256':pr['sha256'],'image_info':pr['info'],'subtracted_background':options.psf_background}
            else:
                if any(s is None for s in spacing) or options.sigma_xy_um is None or (d['Z']>1 and options.sigma_z_um is None):raise ImageError('Provide calibrated XY/Z spacing and explicit Gaussian PSF widths in micrometers, or select a measured PSF.')
                sigmas=[(options.sigma_z_um if a=='Z' else options.sigma_xy_um)/s for a,s in zip(axes,spacing)];kernel=gaussian_psf(sigmas);psf_record={'kind':'estimated Gaussian; not bead calibrated','sigma_source_voxels':sigmas,'sigma_xy_um':options.sigma_xy_um,'sigma_z_um':options.sigma_z_um}
            padded_shape=np.asarray([d[a] for a in axes])+np.asarray(kernel.shape)-1
            if int(np.prod(padded_shape))*4*10>2*1024**3:raise ImageError('Estimated padded deconvolution working memory exceeds the current 2 GiB budget. Use a smaller acquisition/PSF; tiled deconvolution is not implicit.')
            if kernel.sum()<=0:raise ImageError('PSF is empty after background subtraction.')
            kernel=kernel/kernel.sum(dtype=np.float64);psf_record.update(shape=list(kernel.shape),sha256=sha256(kernel.tobytes()).hexdigest(),normalization='unit summed mass')
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc
        def work(ident,folder,checkpoint,update):
            if digest(source/'source.tiff')!=record['sha256']:raise ImageError('Source checksum changed.')
            target=root/'results'/ident;target.mkdir(parents=True,exist_ok=True);planes={}
            for c in range(d['C']):
                raw=np.stack([read_plane(source/'source.tiff',info,c,z) for z in range(d['Z'])]);volume=raw if d['Z']>1 else raw[0]
                corrected=richardson_lucy_reflect(volume,kernel,options.iterations,checkpoint,lambda iteration:update(progress=(c+iteration/options.iterations)/d['C'],message=f'Deconvolving channel {c+1}, iteration {iteration}/{options.iterations}'))
                if d['Z']==1:corrected=corrected[None]
                for z in range(d['Z']):
                    checkpoint();key=plane_key(raw[z],c,z);p=target/(key+'.npy');np.save(p,corrected[z].astype(np.float32),allow_pickle=False);planes[key]={'z_indices':planes.get(key,{}).get('z_indices',[])+[z],'channel':c,'sha256':digest(p)}
            save_json(target/'manifest.json',{'schema':'organelle-restored-1','id':ident,'method':'Richardson-Lucy deconvolution','source_sha256':record['sha256'],'image_id':record['id'],'image_info':record['info'],'psf':psf_record,'inference':options.model_dump(),'planes':planes,'created':utc(),'order':'Richardson-Lucy on raw native intensities, reflected padding by PSF radius, Poisson likelihood conditional on a spatially invariant PSF; cropped back to source dimensions. No claim of recovered molecular resolution.'});update(result_id=ident)
        return start('deconvolve',options,work,needs_n2v=False)

    @app.get('/api/restoration/models/{ident}/download',dependencies=[Depends(authorized)])
    def export_model(ident:str):
        folder,_=model(ident);buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
            for name in ['manifest.json','weights.npz']:z.write(folder/name,name)
        return Response(buf.getvalue(),media_type='application/zip',headers={'Content-Disposition':f'attachment; filename="OrganelleScope-N2V-{ident}.zip"'})
    @app.post('/api/restoration/models/import',dependencies=[Depends(authorized)])
    def import_model(file:UploadFile=File(...)):
        payload=file.file.read(64*1024**2+1)
        if len(payload)>64*1024**2:raise HTTPException(422,'Model bundle exceeds 64 MiB.')
        ident=str(uuid4());folder=path('models',ident)
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                if len(z.namelist())!=2 or set(z.namelist())!={'manifest.json','weights.npz'} or z.getinfo('manifest.json').file_size>1024**2 or any(i.file_size>128*1024**2 for i in z.infolist()):raise ImageError('Select an OrganelleScope tensor-only Noise2Void bundle.')
                meta=z.read('manifest.json');weights=z.read('weights.npz')
            manifest=json.loads(meta)
            if manifest.get('schema')!='organelle-n2v-1' or manifest.get('careamics_version')!='0.3.4' or sha256(weights).hexdigest()!=manifest['weights_sha256']:raise ImageError('Model manifest/checksum/version mismatch.')
            with zipfile.ZipFile(io.BytesIO(weights)) as z:
                if sum(i.file_size for i in z.infolist())>128*1024**2:raise ImageError('Unpacked tensors exceed 128 MiB.')
            with np.load(io.BytesIO(weights),allow_pickle=False) as arrays:
                if any(a.dtype.kind not in 'fi' or not np.isfinite(a).all() for a in (arrays[k] for k in arrays.files)):raise ImageError('Invalid numeric model tensors.')
            TrainOptions.model_validate(manifest['parameters'])
            channels=manifest.get('channels')
            if type(channels) is not int or not 1<=channels<=4 or manifest.get('bit_depth') not in (8,16) or not isinstance(manifest.get('name'),str):raise ImageError('Invalid model channels, name or bit depth.')
            norm=manifest.get('normalization',{})
            for key in ('means','stds'):
                values=norm.get(key,[])
                if len(values)!=channels or not np.isfinite(values).all() or key=='stds' and min(values)<=0:raise ImageError('Invalid training normalization.')
            folder.mkdir(parents=True);(folder/'weights.npz').write_bytes(weights)
            manifest.update(id=ident,imported=utc());save_json(folder/'manifest.json',manifest)
            # Architecture/state compatibility is checked again before inference; never unpickle uploads.
            return manifest
        except Exception as exc:
            shutil.rmtree(folder,ignore_errors=True);raise HTTPException(422,str(exc)) from exc
