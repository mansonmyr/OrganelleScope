"""Independent image queues, frozen analysis runs and review before measurement."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from threading import Event, RLock, Thread
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from organelle_scope import __version__
from organelle_scope.analysis_service import compute_analysis
from organelle_scope.batch_design import summarize_design
from organelle_scope.image_io import ImageInfo
from organelle_scope.roi_analysis import AnalysisRequest, AreaROI


def now():
    return datetime.now(timezone.utc).isoformat()


class DraftAnalysis(AnalysisRequest):
    rois: list[AreaROI] = Field(default_factory=list, max_length=100)


class BatchItem(BaseModel):
    image_id: str
    analysis: DraftAnalysis
    reviewed: bool = False
    experiment: str = Field(default='', max_length=200)
    cell: str = Field(default='', max_length=200)
    condition: str = Field(default='', max_length=200)


class BatchDraft(BaseModel):
    name: str = Field(default='Untitled batch', min_length=1, max_length=200)
    revision: int = Field(default=0, ge=0)
    items: list[BatchItem] = Field(min_length=1, max_length=50)


class RunRequest(BaseModel):
    session_id: str
    revision: int


class Cancelled(Exception):
    pass


def register_batch(app, data_dir, stored, image_dir, authorized):
    root = data_dir / 'batch-data'
    lock = RLock()
    events = {}

    def path(kind, ident):
        try: UUID(ident)
        except ValueError: raise HTTPException(404, 'Batch not found.')
        return root / kind / f'{ident}.json'

    def read(kind, ident):
        p = path(kind, ident)
        if not p.is_file(): raise HTTPException(404, 'Batch not found.')
        return json.loads(p.read_text())

    def save(kind, value):
        p = path(kind, value['id'])
        p.parent.mkdir(parents=True,exist_ok=True)
        tmp = p.with_suffix('.tmp')
        tmp.write_text(json.dumps(value, allow_nan=False))
        tmp.replace(p)

    # A restarted process never silently resumes partially completed measurements.
    for p in (root / 'runs').glob('*.json'):
        run = json.loads(p.read_text())
        if run['status'] in ('running', 'cancelling'):
            run.update(status='interrupted', finished=now())
            for item in run['items']:
                if item['status'] in ('running', 'pending'): item['status'] = 'interrupted'
            save('runs', run)

    @app.get('/api/batch/sessions', dependencies=[Depends(authorized)])
    def sessions():
        with lock:
            values = [json.loads(p.read_text()) for p in (root / 'sessions').glob('*.json')]
            return [{'id':v['id'], 'name':v['name'], 'revision':v['revision']} for v in sorted(values,key=lambda v:v['updated'],reverse=True)]

    @app.get('/api/batch/sessions/{ident}', dependencies=[Depends(authorized)])
    def session(ident:str):
        with lock: return read('sessions', ident)

    def persist(draft, ident=None):
        if len({i.image_id for i in draft.items}) != len(draft.items):
            raise HTTPException(422, 'Each image can occur only once in a batch.')
        with lock:
            previous = read('sessions', ident) if ident else None
            if draft.revision != (previous['revision'] if previous else 0):
                raise HTTPException(409, 'This batch changed. Reopen it before saving.')
            old = {i['image_id']:i for i in previous['items']} if previous else {}
            items=[]
            for item in draft.items:
                _, record, _ = stored(item.image_id)
                value=item.model_dump();value['image']=deepcopy(record)
                # Changed image metadata/channel identity must be reviewed again against the preview.
                if item.image_id in old and old[item.image_id]['image'] != record:
                    value['reviewed']=False
                items.append(value)
            result={'id':ident or str(uuid4()),'name':draft.name,'revision':draft.revision+1,'updated':now(),'items':items}
            save('sessions',result)
            return result

    @app.post('/api/batch/sessions', dependencies=[Depends(authorized)])
    def create(draft:BatchDraft): return persist(draft)

    @app.post('/api/batch/sessions/{ident}', dependencies=[Depends(authorized)])
    def update(ident:str,draft:BatchDraft): return persist(draft,ident)

    def worker(run,event):
        def check():
            if event.is_set(): raise Cancelled()
        try:
            for item in run['items']:
                check()
                with lock:
                    item['status']='running';save('runs',run)
                try:
                    source=item['image'];folder=image_dir(item['image_id'])
                    digest=hashlib.sha256()
                    with (folder/'source.tiff').open('rb') as stream:
                        while chunk:=stream.read(1024*1024):
                            check();digest.update(chunk)
                    if digest.hexdigest()!=source['sha256']: raise ValueError('Source SHA-256 changed; analysis refused.')
                    info=ImageInfo.model_validate(source['info'])
                    if info.needs_axis_confirmation: raise ValueError('Confirm TIFF axes in Image & ROI before batch analysis.')
                    result=compute_analysis(folder,source,info,AnalysisRequest.model_validate(item['analysis']),check)
                    with lock: item.update(status='completed',result=result)
                except Cancelled: raise
                except Exception as exc:
                    with lock: item.update(status='failed',error=str(exc))
                with lock: save('runs',run)
            with lock:
                run['status']='completed_with_errors' if any(i['status']=='failed' for i in run['items']) else 'completed'
        except Cancelled:
            with lock:
                run['status']='cancelled'
                for item in run['items']:
                    if item['status'] in ('running','pending'): item['status']='cancelled'
        finally:
            with lock:
                run['finished']=now();save('runs',run);events.pop(run['id'],None)

    @app.post('/api/batch/runs', dependencies=[Depends(authorized)])
    def start(options:RunRequest):
        with lock:
            if events: raise HTTPException(409,'Another batch is running. Wait or cancel it first.')
            draft=read('sessions',options.session_id)
            if draft['revision']!=options.revision: raise HTTPException(409,'Batch changed; reopen before running.')
            if not all(i['reviewed'] and i['analysis']['rois'] for i in draft['items']): raise HTTPException(422,'Review the ROIs and settings for every image before analysis.')
            for item in draft['items']:
                _,record,_=stored(item['image_id'])
                if record!=item['image']: raise HTTPException(409,'Image metadata or channel identities changed. Save and review this batch again.')
            run={'id':str(uuid4()),'session_id':draft['id'],'revision':draft['revision'],'name':draft['name'],
                 'app_version':__version__,'started':now(),'status':'running','items':deepcopy(draft['items'])}
            for item in run['items']: item['status']='pending'
            run['design_review']=summarize_design(run['items'])
            save('runs',run);event=Event();events[run['id']]=event
            response=deepcopy(run)
            Thread(target=worker,args=(run,event),daemon=True).start()
            return response

    @app.get('/api/batch/runs', dependencies=[Depends(authorized)])
    def runs():
        with lock:
            values=[json.loads(p.read_text()) for p in (root/'runs').glob('*.json')]
            return [{'id':r['id'],'name':r['name'],'status':r['status'],'started':r['started']} for r in sorted(values,key=lambda r:r['started'],reverse=True)]

    @app.get('/api/batch/runs/{ident}', dependencies=[Depends(authorized)])
    def run(ident:str):
        with lock:return read('runs',ident)

    @app.post('/api/batch/runs/{ident}/cancel', dependencies=[Depends(authorized)])
    def cancel(ident:str):
        with lock:
            value=read('runs',ident)
            if ident in events:events[ident].set()
            return value

    @app.get('/api/batch/runs/{ident}/xlsx', dependencies=[Depends(authorized)])
    def excel(ident:str):
        from organelle_scope.excel_export import export_batch
        with lock: value=read('runs',ident)
        if value['status'] in ('running','cancelling'):raise HTTPException(409,'Wait for completion or cancellation before exporting.')
        try: content=export_batch(value)
        except ValueError as exc: raise HTTPException(422,str(exc)) from exc
        return Response(content,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
