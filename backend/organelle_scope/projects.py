"""Versioned local project snapshots with atomic writes and optimistic revisions."""
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4
from fastapi import Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field, JsonValue
from organelle_scope import __version__


class ProjectSave(BaseModel):
    name: str = Field(min_length=1,max_length=120)
    image_id: str | None = None
    expected_image_info: dict[str,JsonValue] | None = None
    state: dict[str,JsonValue]
    expected_revision: int | None = Field(default=None,ge=1)


def register_projects(app,data_dir,stored,authorized):
    root=data_dir.parent/'project-data';root.mkdir(parents=True,exist_ok=True)
    lock=Lock()

    def path_for(project_id):
        try:UUID(project_id)
        except ValueError:raise HTTPException(404,'Project not found.')
        return root/(project_id+'.json')

    def load(project_id):
        path=path_for(project_id)
        if not path.exists():raise HTTPException(404,'Project not found.')
        try:record=json.loads(path.read_text())
        except (ValueError,OSError) as exc:raise HTTPException(422,'Project metadata cannot be read. Restore it from a backup.') from exc
        if not isinstance(record,dict) or record.get('schema_version')!=1:raise HTTPException(422,'This project format is not supported by this application version.')
        return record

    def file_digest(path):
        h=hashlib.sha256()
        with path.open('rb') as stream:
            while chunk:=stream.read(1024**2):h.update(chunk)
        return h.hexdigest()

    def write(path,record):
        text=json.dumps(record,indent=2,allow_nan=False)
        if len(text.encode())>16*1024*1024:raise HTTPException(422,'The project exceeds the current 16 MiB metadata/report limit.')
        temp=path.with_suffix('.'+str(uuid4())+'.tmp');temp.write_text(text);temp.replace(path)

    def save(project_id,options,previous=None):
        try:
            if not options.name.strip():raise ValueError('Provide a project name.')
            json.dumps(options.state,allow_nan=False)
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc
        image=stored(options.image_id)[1] if options.image_id else None
        if image and options.expected_image_info is None:raise HTTPException(422,'Image metadata is required when saving an image project.')
        if image and image['info']!=options.expected_image_info:raise HTTPException(409,'Image import settings changed in another window. Reopen the import before saving this project.')
        if previous and options.expected_revision!=previous['revision']:
            raise HTTPException(409,'This project changed in another window. Reopen it before saving again.')
        now=datetime.now(timezone.utc).isoformat()
        record={'schema_version':1,'id':project_id,'name':options.name.strip(),'revision':previous['revision']+1 if previous else 1,
                'created_utc':previous['created_utc'] if previous else now,'updated_utc':now,'application_version':__version__,
                'image':image,'state':options.state}
        write(path_for(project_id),record)
        return record

    @app.get('/api/projects',dependencies=[Depends(authorized)])
    def list_projects():
        records=[]
        for path in sorted(root.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]:
            try:

                if path.stem=='recovery-latest':continue
                r=load(path.stem);records.append({k:r[k] for k in ('id','name','revision','updated_utc')})
            except (ValueError,KeyError,HTTPException):continue
        return records

    @app.post('/api/projects',dependencies=[Depends(authorized)])
    def create(options:ProjectSave):
        with lock:return save(str(uuid4()),options)

    @app.post('/api/projects/{project_id}',dependencies=[Depends(authorized)])
    def update(project_id:str,options:ProjectSave):
        with lock:return save(project_id,options,load(project_id))

    @app.get('/api/projects/{project_id}',dependencies=[Depends(authorized)])
    def open_project(project_id:str):
        with lock:
            record=load(project_id);snapshot=record.get('image')
            if snapshot:
                folder,current,_=stored(snapshot['id'])
                digest=hashlib.sha256()
                if not (folder/'source.tiff').is_file():raise HTTPException(404,'The project source TIFF is missing. Restore its local image store from a backup.')
                with (folder/'source.tiff').open('rb') as source:
                    for chunk in iter(lambda:source.read(1024*1024),b''):digest.update(chunk)
                if digest.hexdigest()!=snapshot['sha256']:raise HTTPException(409,'Project source bytes changed. Restore the original imported TIFF before reopening.')
                if current['info']!=snapshot['info']:
                    # Restore saved calibration/axes in an isolated import without changing another project's settings.
                    new_id=str(uuid4());destination=data_dir/new_id;destination.mkdir()
                    try:
                        try:os.link(folder/'source.tiff',destination/'source.tiff')
                        except OSError:shutil.copyfile(folder/'source.tiff',destination/'source.tiff')
                        snapshot={**snapshot,'id':new_id}
                        (destination/'metadata.json').write_text(json.dumps(snapshot,indent=2,allow_nan=False))
                    except Exception:
                        shutil.rmtree(destination);raise
                    record['image']=snapshot
                    # Keep the resolved immutable source association for subsequent opens.
                    write(path_for(project_id),record)
            return record

    @app.post('/api/recovery',dependencies=[Depends(authorized)])
    def save_recovery(options:ProjectSave):
        with lock:
            image=stored(options.image_id)[1] if options.image_id else None
            if image and image['info']!=options.expected_image_info:raise HTTPException(409,'Import metadata changed; refresh before recovery autosave.')
            record={'schema_version':1,'id':'recovery','name':options.name,'revision':1,'created_utc':datetime.now(timezone.utc).isoformat(),'updated_utc':datetime.now(timezone.utc).isoformat(),'application_version':__version__,'image':image,'state':options.state}
            from organelle_scope.legacy_artifacts import has_retired_processing
            previous=root/'recovery-latest.json'
            if previous.is_file():
                old=json.loads(previous.read_text())
                if has_retired_processing(old.get('state',{})):
                    ident=str(uuid4());old.update(id=ident,name=old['name']+' (historical recovery)');write(path_for(ident),old)
            write(root/'recovery-latest.json',record)
            return {'updated_utc':record['updated_utc']}

    @app.get('/api/recovery',dependencies=[Depends(authorized)])
    def read_recovery():
        p=root/'recovery-latest.json'
        if not p.is_file():return None
        record=json.loads(p.read_text());snapshot=record.get('image')
        if snapshot:
            folder,current,_=stored(snapshot['id'])
            if current['info']!=snapshot['info'] or file_digest(folder/'source.tiff')!=snapshot['sha256']:raise HTTPException(409,'Recovery source or import settings changed; open the original project instead.')
        return record

    @app.get('/api/projects/{project_id}/archive',dependencies=[Depends(authorized)])
    def export_archive(project_id:str):
        import tempfile,zipfile
        from fastapi.responses import StreamingResponse
        from organelle_scope.legacy_artifacts import result_manifest
        record=open_project(project_id);stream=tempfile.SpooledTemporaryFile(max_size=8*1024**2)
        try:
            with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('project.json',json.dumps(record,allow_nan=False))
                if record['image']:
                    folder,_,_=stored(record['image']['id']);archive.write(folder/'source.tiff','source.tiff')
                ids=set()
                def find(value):
                    if isinstance(value,dict):
                        if value.get('restoration_result_id'):ids.add(value['restoration_result_id'])
                        for v in value.values():find(v)
                    elif isinstance(value,list):
                        for v in value:find(v)
                find(record['state'])
                for ident in ids:
                    manifest=result_manifest(data_dir,ident);folder=data_dir/'restoration-data'/'results'/ident
                    archive.write(folder/'manifest.json',f'restoration/{ident}/manifest.json')
                    for key,entry in manifest['planes'].items():
                        filename=folder/(key+'.npy')
                        if file_digest(filename)!=entry['sha256']:raise ValueError('Restoration integrity check failed.')
                        archive.write(filename,f'restoration/{ident}/{key}.npy')
            stream.seek(0)
            def chunks():
                try:
                    while chunk:=stream.read(1024**2):yield chunk
                finally:stream.close()
            return StreamingResponse(chunks(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="OrganelleScope-project.zip"'})
        except Exception:stream.close();raise

    @app.post('/api/project-archives/import',dependencies=[Depends(authorized)])
    def import_archive(file:UploadFile=File(...)):
        import zipfile,re
        from organelle_scope.image_io import inspect_tiff
        from organelle_scope.processing import ProcessingConfig
        image_id=str(uuid4());project_id=str(uuid4());folder=data_dir/image_id;created=[]
        try:
            with zipfile.ZipFile(file.file) as archive:
                entries=archive.infolist();names=[e.filename for e in entries]
                if len(names)!=len(set(names)) or len(names)>5000 or sum(e.file_size for e in entries)>8*1024**3:raise ValueError('Duplicate entries or archive size/count limit exceeded.')
                if 'project.json' not in names or archive.getinfo('project.json').file_size>16*1024**2:raise ValueError('Missing or oversized project metadata.')
                if any(n not in ('project.json','source.tiff') and not re.fullmatch(r'restoration/[0-9a-f-]{36}/(?:manifest\.json|[0-3]-(?:z[0-9]+-)?[0-9a-f]{64}\.npy)',n) for n in names):raise ValueError('Unexpected archive entry; only project data and verified float artifacts are accepted.')
                if shutil.disk_usage(data_dir).free<sum(e.file_size for e in entries)+256*1024**2:raise ValueError('Insufficient free disk space for the project archive.')
                record=json.loads(archive.read('project.json'));options=ProjectSave(name=record['name'],state=record['state']);image=record.get('image');mapping={}
                if image:
                    folder.mkdir();created.append(folder)
                    with archive.open('source.tiff') as source,(folder/'source.tiff').open('wb') as destination:shutil.copyfileobj(source,destination,1024**2)
                    digest=hashlib.sha256()
                    with (folder/'source.tiff').open('rb') as source:
                        while chunk:=source.read(1024**2):digest.update(chunk)
                    if digest.hexdigest()!=image['sha256']:raise ValueError('Source TIFF checksum mismatch.')
                    settings=image.get('options',{});info=inspect_tiff(folder/'source.tiff',settings.get('series_index',0),settings.get('axes'),settings.get('spacing_um',{}));info.filename=Path(image['info']['filename']).name
                    if info.model_dump()!=image['info']:raise ValueError('Archive metadata does not match inspected source and recorded calibration.')
                    mapping[image['id']]=image_id;image={**image,'id':image_id,'info':info.model_dump(),'import_schema':2};(folder/'metadata.json').write_text(json.dumps(image,allow_nan=False))
                for old in {n.split('/')[1] for n in names if n.startswith('restoration/')}:
                    UUID(old);new=str(uuid4());mapping[old]=new;destination=data_dir/'restoration-data'/'results'/new;destination.mkdir(parents=True);created.append(destination)
                    manifest=json.loads(archive.read(f'restoration/{old}/manifest.json'))
                    if not image or manifest['source_sha256']!=image['sha256']:raise ValueError('Restoration source does not match archive image.')
                    for key,entry in manifest['planes'].items():
                        if not re.fullmatch(r'[0-3]-(?:z[0-9]+-)?[0-9a-f]{64}',key):raise ValueError('Invalid artifact key.')
                        path=destination/(key+'.npy')
                        with archive.open(f'restoration/{old}/{key}.npy') as source,path.open('wb') as out:shutil.copyfileobj(source,out,1024**2)
                        if file_digest(path)!=entry['sha256']:raise ValueError('Restoration checksum mismatch.')
                    manifest.update(id=new,image_id=image_id);(destination/'manifest.json').write_text(json.dumps(manifest,allow_nan=False))
                def remap(v):
                    if isinstance(v,dict):return {k:remap(x) for k,x in v.items()}
                    if isinstance(v,list):return [remap(x) for x in v]
                    return mapping.get(v,v) if isinstance(v,str) else v
                options.state=remap(options.state);options.image_id=image_id if image else None;options.expected_image_info=image['info'] if image else None
                legacy_config=options.state.get('core',{}).get('processing',{})
                ProcessingConfig.model_validate({**legacy_config,'restoration_result_id':None})
                legacy_result=legacy_config.get('restoration_result_id')
                if legacy_result and legacy_result not in mapping.values():raise ValueError('Archive is missing its active restoration result.')
                with lock:return save(project_id,options)
        except Exception as exc:
            for p in created:shutil.rmtree(p,ignore_errors=True)
            if isinstance(exc,HTTPException):raise
            raise HTTPException(422,str(exc)) from exc
        finally:file.file.close()

    return open_project
