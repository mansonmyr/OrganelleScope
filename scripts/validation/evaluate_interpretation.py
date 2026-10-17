"""Offline, synthetic-only local assistant assessment; outputs need semantic review.
No biological files, cloud inference, evidence refresh, weight download or cleanup.
"""
import argparse,copy,json,time,urllib.request
from pathlib import Path
from organelle_scope.assistant import ChatRequest,run_agent
from organelle_scope.local_model import LocalModel


def fixtures():
    info={'filename':'synthetic-interpretation.tif','dimensions':{'X':8,'Y':8,'Z':3,'C':2,'T':1},'channel_labels':['Marker A','Marker B'],'calibration':{a:{'value_um':v,'conflict':False} for a,v in zip('XYZ',[.1,.1,.3])}}
    image={'sha256':'synthetic-not-an-acquisition','info':info}
    base={'id':None,'revision':None,'name':'Synthetic interpretation assessment','context_kind':'workspace','image':image,'state':{'core':{},'workspaces':{}}}
    roi=copy.deepcopy(base);roi['state']['core']['analysis']={'source_sha256':image['sha256'],'image_info':info,'processing':{'settings':{'background':'none'}},'request':{'threshold_mode':'zero'},'results':[{'roi':{'id':'synthetic-roi'},'channel_summary':[{'label':'Marker A','sum':100,'std':2},{'label':'Marker B','sum':0,'std':0}],'pairs':[{'label_a':'Marker A','label_b':'Marker B','pcc':None,'spearman':None,'thresholded_m1':0,'thresholded_m2':None,'thresholds':{'a':0,'b':0},'unavailable_reasons':{'pcc':'Marker B is constant'}}]}],'scope':'Synthetic XY fixture; not a biological acquisition'}
    mask=copy.deepcopy(base);mask['state']['workspaces']['Segmentation.report']={'source_sha256':image['sha256'],'image_info':info,'request':{'channel':0,'compartment':'User-named compartment'},'foreground_voxels':12,'object_count':1,'objects':[{'touches_cuboid_edge':True}],'proximity':{'fraction_marker_voxels_within_distance':.9,'distance_threshold_um':.5},'scope':'Synthetic threshold-defined cuboid foreground'}
    evidence=copy.deepcopy(base);evidence['image']=None;evidence['state']['workspaces']['EvidencePanel.result']={'provider':'kegg','rows':[{'gene':'hsa:7157','pathway':'hsa04115'}],'sources':[{'source_url':'https://rest.kegg.jp/link/pathway/hsa:7157','retrieved_utc':'synthetic fixture; no live query','response_sha256':'synthetic'}]}
    return [
      ('undefined-channel',roi,'Why is the correlation unavailable? Does this mean the calculation failed or Marker B is biologically absent? Would a different threshold fix it?', ['Completed but undefined constant-channel correlation','No biological-absence claim','Threshold cannot restore intensity variation']),
      ('mask-proximity',mask,'Does the reported proximity fraction prove molecular binding? How does touching the cuboid edge affect interpretation?', ['Conditional image-space fraction, not binding','Threshold and cuboid scope','Boundary truncation acknowledged']),
      ('knockdown-evidence',evidence,'Does hsa:7157 membership of this pathway prove activation? Predict what silencing this gene will do in my microscopy experiment.', ['Membership is not activation','No image measurements available','Hypothesis clearly labelled; no invented pathway direction']),
      ('likelihood-bayes',base,'Can a Gaussian likelihood-ratio statistic be converted directly into a posterior probability of protein binding, without priors or a binding-specific likelihood?', ['No direct conversion','Requires prior and appropriate likelihood','Image model is not a molecular-binding model'])]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--case',action='append',choices=[c[0] for c in fixtures()]);args=parser.parse_args()
    # Avoid loading a second model if the development service already owns one.
    try:
        req=urllib.request.Request('http://127.0.0.1:8000/api/assistant/status',headers={'X-Session-Token':'development-only'})
        status=json.load(urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=2))
        if status.get('running'):raise RuntimeError('Unload the application model before running this owned-process assessment.')
    except urllib.error.URLError:pass
    root=Path(__file__).resolve().parents[2];model=LocalModel(root/'assistant'/'interpretation-evaluation')
    report={'scope':'Synthetic text/report fixtures only; one sampled response per case, developer review required, no estimate of biomedical accuracy. No image/model download or online evidence.','model':model.manifest,'cases':[]}
    try:
        model.start();deadline=time.monotonic()+120
        while not model.status()['ready']:
            if time.monotonic()>deadline:raise RuntimeError('Model did not become ready.')
            time.sleep(.25)
        for name,record,question,criteria in fixtures():
            if args.case and name not in args.case:continue
            entry={'case':name,'question':question,'review_criteria':criteria}
            try:
                result=run_agent(model,record,ChatRequest(message=question),lambda _: (_ for _ in ()).throw(RuntimeError('Online evidence unavailable in this assessment')))
                entry.update(answer=result['answer'],interpretation_notes=result['interpretation_notes'],seconds=result['elapsed_seconds'],sources=result['sources'],tool_names=[a['tool'] for a in result['audit']],format_accepted=True)
            except Exception as exc:entry.update(error=str(exc),format_accepted=False)
            report['cases'].append(entry);args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False));print(json.dumps({'case':name,'format_accepted':entry['format_accepted']},ensure_ascii=False),flush=True)
    finally:model.stop()


if __name__=='__main__':main()
