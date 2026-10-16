"""Versioned local project snapshots with atomic writes and optimistic revisions."""
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import UUID, uuid4
from fastapi import Depends, HTTPException
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

    return open_project
