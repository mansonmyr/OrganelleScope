"""Session-scoped ROI jobs with cooperative cancellation and bounded result retention."""
from copy import deepcopy
from threading import Event, RLock, Thread
from time import perf_counter
from uuid import uuid4

from fastapi import Depends, HTTPException
from organelle_scope.analysis_service import compute_analysis,save_analysis
from organelle_scope.image_io import ImageError
from organelle_scope.roi_analysis import AnalysisRequest


class AnalysisCancelled(Exception):
    pass


def register_analysis_jobs(app, stored, authorized):
    lock=RLock();jobs={};events={}

    def lookup(ident):
        if ident not in jobs:raise HTTPException(404,'Analysis job not found; jobs are local to this running session.')
        return jobs[ident]

    @app.post('/api/images/{image_id}/analysis-jobs',dependencies=[Depends(authorized)])
    def start(image_id:str, options:AnalysisRequest):
        folder,record,info=stored(image_id)
        with lock:
            if events:raise HTTPException(409,'Another ROI calculation is running. Wait or cancel it first.')
            # Keep at most five reports in memory; research exports/projects are untouched.
            while len(jobs)>=5:jobs.pop(next(iter(jobs)))
            ident=str(uuid4());event=Event();events[ident]=event
            job={'id':ident,'image_id':image_id,'status':'running','progress':{'completed':0,'total':0,'stage':'Starting'}}
            jobs[ident]=job
            def check():
                if event.is_set():raise AnalysisCancelled()
            def progress(**values):
                with lock:job['progress']=values
            def worker():
                began=perf_counter()
                try:
                    result=compute_analysis(folder,record,info,options,check,progress)
                    with lock:
                        check()
                        if stored(image_id)[1]!=record:raise ImageError('Image settings changed; result was not saved. Recalculate using current settings.')
                        # Save only a finished, uncancelled result; the prior result survives failure/cancellation.
                        save_analysis(folder,result)
                        job.update(status='completed',result=result)
                except AnalysisCancelled:
                    with lock:job.update(status='cancelled')
                except Exception as exc:
                    with lock:job.update(status='failed',error=str(exc))
                finally:
                    with lock:job['elapsed_seconds']=perf_counter()-began;events.pop(ident,None)
            response=deepcopy(job)
            Thread(target=worker,daemon=True).start()
            return response

    @app.get('/api/analysis-jobs/{ident}',dependencies=[Depends(authorized)])
    def status(ident:str):
        with lock:return deepcopy(lookup(ident))

    @app.post('/api/analysis-jobs/{ident}/cancel',dependencies=[Depends(authorized)])
    def cancel(ident:str):
        with lock:
            job=lookup(ident)
            if ident in events:events[ident].set();job['status']='cancelling'
            return deepcopy(job)
