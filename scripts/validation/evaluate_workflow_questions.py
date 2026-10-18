"""New synthetic workflow questions, frozen before inference; no private images or cloud."""
import argparse,copy,hashlib,json
from pathlib import Path
from evaluate_interpretation import fixtures
from organelle_scope.assistant import ChatRequest,run_agent,ensure_ready
from organelle_scope.local_model import LocalModel


def cases():
    overlap=copy.deepcopy(fixtures()[0][1]);row=overlap['state']['core']['analysis']['results'][0]
    row['channel_summary'][1].update(sum=100,std=3)
    row['pairs'][0].update(pcc=-.3,spearman=-.2,thresholded_m1=.92,thresholded_m2=.95,unavailable_reasons={})
    sampling=copy.deepcopy(fixtures()[3][1]);sampling['image']=copy.deepcopy(overlap['image']);sampling['state']['workspaces']={}
    sampling['state']['workspaces']['ChannelPanel.quality']={'source_sha256':sampling['image']['sha256'],'image_info':sampling['image']['info'],'z':0,'channels':[], 'sampling_review':{'registration':'not measured','axes':[{'axis':'X','spacing_um':.1,'declared_resolution_um':.2,'samples_per_declared_resolution':2,'status':'at least two samples per supplied resolution'}]},'scope':'Selected XY plane only; nominal resolution is user supplied, not measured.'}
    return [
        {'id':'overlap-versus-covariation','record':overlap,'question':'The overlap fractions look almost complete while both correlations are negative. Which result should I trust, and does one invalidate the other?','criteria':['Different metric definitions can coexist','Do not call either calculation invalid solely from this disagreement','Review threshold/background and regions; no binding inference']},
        {'id':'sampling-versus-resolution','record':sampling,'question':'The acquisition panel passes the two-samples screen. Does that verify my optical resolution and registration throughout the stack? What evidence is still missing?','criteria':['User supplied nominal resolution is not measured optical resolution','Registration has not been measured','Selected plane cannot certify the full stack']},
        {'id':'choosing-best-sensitivity','record':fixtures()[3][1],'question':'One threshold variant gives the largest colocalization. Should I report only that setting and treat the other variants as independent replicates?','criteria':['Avoid selecting settings solely to maximise favourable overlap','Sensitivity variants are not independent biological experiments','Do not invent supplied sweep results']},
        {'id':'recovery-is-not-replication','record':fixtures()[3][1],'question':'If a failed image succeeds in a recovery batch, can I combine both attempts as additional biological experiments? How should I retain the failed attempt?','criteria':['Repeated processing of one source does not add independent experiments','Preserve provenance of original attempt','Do not invent completed attempts in this context']},
    ]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--followup',action='store_true');p.add_argument('--case',action='append');args=p.parse_args()
    if args.output.exists():raise ValueError('Keep the initial assessment; choose a new output for a repeat.')
    root=Path(__file__).resolve().parents[2];suite=cases()
    report={'scope':'Developer-authored synthetic questions frozen before first inference. One sampled answer per case, same model generation and review. Descriptive semantic assessment, not independent biological validation or a general accuracy estimate. No private images, online refresh or new model download.', 'suite_sha256':hashlib.sha256(json.dumps(suite,sort_keys=True).encode()).hexdigest(),'frozen_cases':suite,'followup_after_development':args.followup,'implementation_sha256':{name:hashlib.sha256((root/'backend/organelle_scope'/name).read_bytes()).hexdigest() for name in ['assistant.py','interpretation.py','claim_review.py']},'cases':[]}
    if args.followup:report['scope']='Follow-up diagnostic after adding documented workflow definitions. These questions have already been seen; not a fresh held-out assessment. Same model generates and audits. No private images or online lookup.'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def save():args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    save();model=LocalModel(root/'assistant/workflow-assessment');report['model']=model.manifest
    try:
        ensure_ready(model)
        for case in suite:
            if args.case and case['id'] not in args.case:continue
            entry={'id':case['id'],'semantic_review':'pending'}
            try:
                result=run_agent(model,case['record'],ChatRequest(message=case['question']),lambda _: (_ for _ in ()).throw(ValueError('Online lookup disabled for assessment')))
                entry.update(answer=result['answer'],claim_review=result.get('evidence_review'),question_coverage=result.get('question_coverage'),recorded_quantities=result.get('recorded_quantities'),seconds=result['elapsed_seconds'],audit=result['audit'])
            except Exception as exc:entry.update(error=str(exc),details=getattr(exc,'details',None))
            report['cases'].append(entry);save();print(case['id'],'answer' if 'answer' in entry else 'withheld/error',flush=True)
    finally:model.stop();save()
if __name__=='__main__':main()
