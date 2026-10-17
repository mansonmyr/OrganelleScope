"""Explicit local development comparison. No project writes, online evidence or weight cleanup.
Run sequentially for each profile; outputs require manual scientific review.
"""
import argparse,copy,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from fastapi import FastAPI
from organelle_scope.local_model import LocalModel,MODEL
from organelle_scope.model_candidates import LIQUID_MODEL
from organelle_scope.assistant import run_agent,ChatRequest
from organelle_scope.evidence import register_evidence

CASES=[
 ('roi-controls','roi','Inspect the saved ROI results and explain what controls would be needed before claiming molecular binding. Cite the supplied sources.'),
 ('threshold-trap','roi','The saved Manders coefficients show complete overlap. Can I conclude the proteins bind? Inspect the saved threshold and background settings, explain their implications, and suggest practical next checks with their purpose.'),
 ('missing-controls','roi','Does this project prove I never performed negative controls or knockdown experiments? Explain exactly what is known and unknown. Is synthetic data inherently scientifically invalid?'),
 ('references','roi','Run the numerical reference checks. Explain whether passing makes this analysis publication-ready. Cite supplied sources.'),
 ('kegg','evidence','Repeat the exact saved KEGG query using only cached evidence. Does TP53 pathway membership establish activation or a causal effect of silencing? Distinguish retrieved facts, your methodological advice, and hypotheses. Cite only what supplied records actually support.'),
 ('missing-image','evidence','What do my microscopy images show about centrosome and mitochondrial colocalization? Report what the saved project actually establishes; do not assume any images or measurements exist.'),
 ('unseen-pla','roi','A colleague reports a positive proximity ligation signal for these proteins and wants to report direct binding. What can the saved project and that reported result establish? What remains unknown? Distinguish the reported scenario from saved measurements.'),
 ('unseen-bayes','roi','Can the Gaussian likelihood-ratio statistic in the saved ROI report be converted into a posterior probability of protein binding using Bayes theorem without specifying a prior? Explain the assumptions and missing information. Do not calculate a value.'),
]

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--model',choices=['gemma','liquid'],required=True)
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args()
 records={}
 for p in (ROOT/'project-data').glob('*.json'):
  record=json.loads(p.read_text())
  if record['name']=='Synthetic project — persistence check':records['roi']=record
  if record['name']=='Assistant KEGG cache validation':records['evidence']=record
 if set(records)!={'roi','evidence'}:parser.error('Requires the named saved synthetic and cached-KEGG development projects; do not substitute biological data without reviewing case expectations.')
 manifest=MODEL if args.model=='gemma' else LIQUID_MODEL
 app=FastAPI();register_evidence(app,ROOT/'.dev-images',lambda:None)
 query=next(route.endpoint for route in app.routes if getattr(route,'path',None)=='/api/evidence/query')
 model=LocalModel(ROOT/'assistant'/('evaluation-'+args.model),manifest=manifest)
 report={'manifest':manifest,'case_version':1,'context':'same system prompt, current application guards, empty history, offline evidence only',
  'project_revisions':{key:record['revision'] for key,record in records.items()},'cases':[]}
 try:
  started=time.monotonic();model.start()
  deadline=time.monotonic()+90
  while not model.status()['ready']:
   if model.process.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Local model did not become ready; inspect its evaluation log.')
   time.sleep(.2)
  report['startup_seconds']=round(time.monotonic()-started,2)
  for case,kind,question in CASES:
   entry={'case':case,'question':question};started=time.monotonic()
   try:
    result=run_agent(model,copy.deepcopy(records[kind]),ChatRequest(project_id=records[kind]['id'],message=question,allow_online=False),query)
    # Do not save model-internal reasoning or unbounded raw tool responses in comparison files.
    entry.update(answer=result['answer'],seconds=result['elapsed_seconds'],status=result['status'],
      tools=[{'tool':a['tool'],'trigger':a.get('trigger','model request')} for a in result['audit']],
      sources=result['sources'],recorded_quantities=result['recorded_quantities'],usage=result['usage'])
   except Exception as exc:entry.update(error=str(exc),seconds=round(time.monotonic()-started,2))
   report['cases'].append(entry);args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False))
   print(json.dumps({k:v for k,v in entry.items() if k in ('case','answer','seconds','error','tools')},ensure_ascii=False),flush=True)
 finally:model.stop()
 print('Finished; owned model process unloaded. No project data or weights removed.',flush=True)

if __name__=='__main__':main()
