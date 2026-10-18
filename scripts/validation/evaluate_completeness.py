"""Fixed complete/incomplete answer pairs: coverage review only, no image inference."""
import argparse,hashlib,json
from pathlib import Path
from organelle_scope.completeness import review_completeness
from organelle_scope.assistant import ensure_ready
from organelle_scope.local_model import LocalModel

CASES=[
 {'id':'empty-mask-incomplete','question':'Why is reference distance unavailable? Does this show absence from the cell?','answer':'The reference mask is empty, so the distance is undefined.','expected':['addressed','unanswered']},
 {'id':'empty-mask-complete','question':'Why is reference distance unavailable? Does this show absence from the cell?','answer':'The reference mask is empty, so the distance is undefined. This cropped mask does not show that the protein is absent from the cell.','expected':['addressed','addressed']},
 {'id':'reverse-incomplete','question':'What weights does proximity use? Must I rerun to obtain the reverse direction?','answer':'Proximity uses equal source-voxel weighting.','expected':['addressed','unanswered']},
 {'id':'reverse-complete','question':'What weights does proximity use? Must I rerun to obtain the reverse direction?','answer':'Proximity uses equal source-voxel weighting. Both directions are already recorded, so no rerun is needed unless you change the measurement settings.','expected':['addressed','addressed']},
]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 if args.output.exists():raise ValueError('Keep the original assessment; use a new output path.')
 root=Path(__file__).resolve().parents[2]
 report={'scope':'Four developer-labelled answer pairs frozen before review. Tests identification of omissions, not generation accuracy, truth or citation entailment. These are controlled diagnostic cases, not unseen microscopy questions or a biomedical accuracy estimate.','suite_sha256':hashlib.sha256(json.dumps(CASES,sort_keys=True).encode()).hexdigest(),'implementation_sha256':hashlib.sha256((root/'backend/organelle_scope/completeness.py').read_bytes()).hexdigest(),'frozen_cases':CASES,'cases':[]}
 def save():args.output.write_text(json.dumps(report,indent=2)+'\n')
 args.output.parent.mkdir(parents=True,exist_ok=True);save();model=LocalModel(root/'assistant/completeness-assessment');report['model']=model.manifest
 try:
  ensure_ready(model)
  for case in CASES:
   review=review_completeness(model,case['question'],case['answer'])
   observed=[p['status'] for p in review.get('parts',[])]
   report['cases'].append({'id':case['id'],'review':review,'expected':case['expected'],'observed':observed,'matches_controlled_labels':observed==case['expected']});save();print(case['id'],observed,flush=True)
 finally:model.stop();save()
if __name__=='__main__':main()
