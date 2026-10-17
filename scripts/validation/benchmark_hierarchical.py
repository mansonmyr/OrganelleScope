"""Audit repeated-sampling behavior under one explicit independent nested design."""
import json
from pathlib import Path
import numpy as np
from organelle_scope.experiments import ExperimentRequest,analyze_experiment
rng=np.random.default_rng(20261017);cases=[]
for n in (3,8):
    covered=reject=0
    for simulation in range(100):
        items=[]
        for condition in ('a','b'):
            for exp in range(n):
                effect=rng.normal(0,1)
                for cell in range(4):
                    mean=effect+rng.normal(0,.5)
                    result={'request':{'threshold_mode':'zero'},'processing':{},'source_sha256':'simulation','results':[{'roi':{'id':'r'},'channel_summary':[{'channel':0,'mean':mean}]}]}
                    items.append({'status':'completed','condition':condition,'experiment':condition+str(exp),'cell':str(cell),'image_id':str(len(items)),'result':result})
        request=ExperimentRequest(run_id='simulation',conditions=['a','b'],design='independent_experiments',metric='mean',iterations=199,seed=simulation)
        c=analyze_experiment({'id':'simulation','items':items},request)['contrasts'][0];lo,hi=c['hierarchical_bootstrap_ci95'];covered+=lo<=0<=hi;reject+=c['permutation_p_two_sided']<=.05
    cases.append({'experiments_per_condition':n,'cells_per_experiment':4,'simulations':100,'bootstrap_coverage_fraction':covered/100,'permutation_false_positive_fraction':reject/100,'minimum_attainable_two_sided_p':c['minimum_attainable_two_sided_p']})
report={'seed':20261017,'bootstrap_draws':199,'true_difference':0,'between_experiment_sd':1,'within_experiment_cell_sd':.5,'cases':cases,'scope':'One Gaussian nested independent-experiment simulation with 100 repetitions per case. Monte Carlo uncertainty is substantial. Percentile bootstrap intervals can under-cover with few independent experiments; minimum p depends on assignment count. This is not validation for every lab design or phenotype.'}
Path('docs/HIERARCHICAL_SYNTHETIC_BENCHMARK.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
