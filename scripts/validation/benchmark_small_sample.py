"""Assess opt-in percentile intervals using the actual nested inference routine.

This is one Gaussian null model, not a general coverage or power certificate.
"""
import argparse,json,sys
from pathlib import Path
import numpy as np
from scipy.stats import binomtest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'backend'))
from organelle_scope.experiments import ExperimentRequest,analyze_experiment


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repetitions',type=int,default=100)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.repetitions<1:parser.error('Use at least one repetition.')
    seed=20261025;rng=np.random.default_rng(seed);summary=[]
    for design in ['independent_experiments','paired_experiments']:
        for n in [3,4,5,6]:
            covered=rejected=0
            for rep in range(args.repetitions):
                shared=rng.normal(0,1,n);items=[]
                for condition in ['a','b']:
                    for experiment in range(n):
                        effect=(shared[experiment] if design=='paired_experiments' else rng.normal(0,1))+rng.normal(0,.5)
                        for cell in range(4):
                            value=effect+rng.normal(0,.5);source=f'{condition}-{experiment}-{cell}'
                            result={'request':{'threshold_mode':'zero'},'processing':{},'source_sha256':source,'image_info':{'channel_labels':['Simulated intensity']},'results':[{'roi':{'id':'r'},'channel_summary':[{'channel':0,'mean':float(value)}]}]}
                            items.append({'status':'completed','condition':condition,'experiment':str(experiment) if design=='paired_experiments' else condition+str(experiment),'cell':str(cell),'image_id':source,'result':result})
                opts=ExperimentRequest(run_id='simulation',conditions=['a','b'],design=design,metric='mean',iterations=999,seed=10000+rep,normal_model=True,exploratory_intervals=True)
                report=analyze_experiment({'id':'simulation','items':items},opts);contrast=report['contrasts'][0]
                lo,hi=contrast['hierarchical_bootstrap_ci95'];covered+=lo<=0<=hi;rejected+=contrast['permutation_p_two_sided']<=.05
            def interval(count):
                ci=binomtest(count,args.repetitions).proportion_ci(.95,method='exact');return [ci.low,ci.high]
            row={'design':design,'experiments_per_condition_or_pairs':n,'simulations':args.repetitions,'interval_coverage':covered/args.repetitions,'coverage_monte_carlo_ci95':interval(covered),'false_positive_fraction':rejected/args.repetitions,'false_positive_monte_carlo_ci95':interval(rejected),'permutation_assignments':contrast['permutation_assignments_possible'],'permutation_exact':contrast['permutation_exact'],'exact_two_sided_floor':contrast['exact_probability_floor']}
            summary.append(row);print(design,n,'coverage',row['interval_coverage'],'rejections',row['false_positive_fraction'],flush=True)
    output={'application_algorithm':'experiment-inference-3','data_seed':seed,'analysis_seed':'10000 + simulation index','bootstrap_draws':999,'true_difference':0,'cells_per_experiment':4,'experiment_sd':1,'condition_specific_experiment_sd':.5,'cell_residual_sd':.5,'paired_model':'The SD-1 experiment effect is shared across paired conditions.','cases':summary,'scope':'One Gaussian hierarchical null family. Percentile coverage can fall below nominal 95%; Monte Carlo intervals quantify simulation precision, not biological uncertainty. No power, heavy-tail, missingness or posterior calibration claim. Exploratory intervals were explicitly enabled; they are off by default in the application. Estimation-only contrasts retain numeric permutation values in exports but are not interpreted as attainable significance tests.'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,indent=2)+'\n')

if __name__=='__main__':main()
