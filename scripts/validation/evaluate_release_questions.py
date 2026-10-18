"""Fixed synthetic questions for the next interpretation assessment. No private data."""
import argparse,copy,hashlib,json
from pathlib import Path
from evaluate_interpretation import fixtures
from organelle_scope.assistant import ChatRequest,run_agent,ensure_ready
from organelle_scope.local_model import LocalModel


def cases():
    identity=copy.deepcopy(fixtures()[0][1])
    info=identity['image']['info'];info['filename']='misleading-protein-name.tif';info['channel_labels']=['Alexa 488','Alexa 568']
    analysis=identity['state']['core']['analysis'];analysis['results'][0]['pairs'][0].update(label_a='Alexa 488',label_b='Alexa 568',pcc=.8,spearman=.7,thresholded_m1=.6,thresholded_m2=.4,unavailable_reasons={})
    analysis['results'][0]['channel_summary']=[{'label':name,'sum':100,'std':3} for name in info['channel_labels']]
    return [
        ('marker-identity',identity,'The filename suggests a protein and the channels have dye names. Can you identify which protein is in each stored channel and interpret binding?', ['Do not infer protein identity from filename/dyes','Request owner/acquisition mapping','Overlap does not establish binding']),
        ('clipping-after-offset',fixtures()[3][1],'I subtracted a constant background and clipped negative pixels to zero. Should Pearson necessarily stay unchanged because a uniform offset is invariant?', ['Distinguish affine offset from nonlinear clipping','No guaranteed invariance after clipping','Recommend raw/processed sensitivity review']),
        ('contradictory-mapping',fixtures()[3][1],'I corrected the channel identities after analysing a batch. Can I reuse the earlier marker-specific assistant interpretation and treat copies of the same TIFF as different independent experiments?', ['Earlier marker-specific interpretation needs revision','Reference-channel selection may need rerun','Copies are not independent experiments'])]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--followup',action='store_true');args=p.parse_args()
    root=Path(__file__).resolve().parents[2];questions=cases()
    report={'followup_after_development':args.followup,'suite_sha256':hashlib.sha256(json.dumps(questions,sort_keys=True).encode()).hexdigest(),'scope':'Fixed before first inference, synthetic-only developer-authored questions. No private images, online lookup or model download. One sampled response per case; semantic review required. This is not an independent held-out microscopy benchmark. Repeating after changes must be labelled a follow-up.', 'implementation_sha256':{name:hashlib.sha256((root/'backend/organelle_scope'/name).read_bytes()).hexdigest() for name in ['assistant.py','interpretation.py','claim_review.py']},'cases':[]}
    if args.followup:report['scope']='Repeated questions after correcting inconsistent synthetic input; follow-up diagnostic, not unseen accuracy assessment. Same local model generates and audits; no private data or online lookup.'
    model=LocalModel(root/'assistant/release-question-assessment');report['model']=model.manifest
    args.output.parent.mkdir(parents=True,exist_ok=True)
    def save():args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    save()
    try:
        ensure_ready(model)
        for name,record,question,criteria in questions:
            entry={'case':name,'question':question,'review_criteria':criteria,'semantic_review':'pending'}
            try:
                result=run_agent(model,record,ChatRequest(message=question),lambda _: (_ for _ in ()).throw(ValueError('Online requests disabled for this evaluation')))
                entry.update(answer=result['answer'],claim_review=result.get('evidence_review'),interpretation_notes=result['interpretation_notes'],seconds=result['elapsed_seconds'],tool_record=result['audit'])
            except Exception as exc:entry.update(error=str(exc),withheld_review=getattr(exc,'details',None))
            report['cases'].append(entry);save();print(name,'completed' if 'answer' in entry else 'withheld/error',flush=True)
    finally:model.stop()

if __name__=='__main__':main()
