"""Adversarial forced-acceptance regression corpus, not a language-model evaluation."""
import argparse,json
from pathlib import Path
from organelle_scope.claim_review import review_claims

SOURCE='Image overlap does not prove binding. A conditional foreground fraction is not a binding probability. Manders intensity fractions are not shared volume. Annotation correction does not provide biological ground truth. Software tests do not certify publication readiness. Pearson measures linear intensity correlation.'
CASES=[
 ('positive-method','Pearson measures linear intensity correlation. [methods]',True),
 ('binding-limitation','Image overlap does not prove binding. [methods]',True),
 ('negation-bypass','Not only does image overlap prove binding. [methods]',False),
 ('mixed-clause','The method does not reduce noise but proves binding. [methods]',False),
 ('positive-binding','The observed overlap proves binding. [methods]',False),
 ('manders-volume','Manders measures shared volume. [methods]',False),
 ('manders-mixed-negation','Manders is not uninformative; it measures shared volume. [methods]',False),
 ('probability-overclaim','The proximity fraction represents the probability of binding. [methods]',False),
 ('probability-limitation','The proximity fraction is not a binding probability. [methods]',True),
 ('readiness-negation','Not only is this publication-ready. [methods]',False),
 ('annotation-negation','Corrected channel labels are not merely useful but biological ground truth. [methods]',False),
]
class ForcedAcceptance:
 def completion(self,*args,**kwargs):
  return {'choices':[{'message':{'content':json.dumps({'claims':[{'index':0,'kind':'record_supported','source_id':'methods','quote':SOURCE}]})},'finish_reason':'stop'}]}

def assess():
 rows=[]
 for name,text,expected in CASES:
  result=review_claims(ForcedAcceptance(),text,{'methods':SOURCE})
  actual=result['retained_sentences']==1
  rows.append({'case':name,'draft':text,'expected_retained':expected,'actual_retained':actual,'matches_expected':actual==expected,'reason':result['claims'][0]['reason']})
 return {'scope':'Developer-labelled adversarial regression sentences. Reviewer is a stub that accepts every claim with a verbatim source quote. Measures deterministic guard behavior only; not model accuracy or general citation entailment.','source':SOURCE,'cases':rows,'matching_cases':sum(r['matches_expected'] for r in rows),'case_count':len(rows)}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 if args.output.exists():raise ValueError('Preserve the original report; use a different output path.')
 report=assess();args.output.write_text(json.dumps(report,indent=2)+'\n');print(report['matching_cases'], '/',report['case_count'])
