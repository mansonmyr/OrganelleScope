"""Independent exact-enumeration and prior-importance-sampling numerical oracles.
Synthetic data; these do not validate a biological design or repeated-sampling coverage.
"""
import argparse,json,itertools,math
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
from organelle_scope.experiments import ExperimentRequest,analyze_experiment,normal_posterior

def run_record(a,b,paired=False):
 items=[]
 for condition,values in [('a',a),('b',b)]:
  for index,value in enumerate(values):
   result={'request':{'threshold_mode':'zero'},'processing':{},'source_sha256':'synthetic','image_info':{'channel_labels':['Synthetic mean']},'results':[{'roi':{'id':'r'},'channel_summary':[{'channel':0,'mean':value}]}]}
   items.append({'status':'completed','condition':condition,'experiment':str(index) if paired else condition+str(index),'cell':'c','image_id':str(len(items)),'result':result})
 return {'id':'oracle','items':items}

def exact_checks():
 cases=[]
 for a,b,paired in [([-1,0,2],[2,3,5],False),([1,2,3],[2,4,7],True),([2,2,2],[2,2,2],False)]:
  af=list(map(Fraction,a));bf=list(map(Fraction,b));observed=sum(bf)/len(bf)-sum(af)/len(af)
  if paired:
   differences=[y-x for x,y in zip(af,bf)]
   distribution=[sum(sign*delta for sign,delta in zip(signs,differences))/len(differences) for signs in itertools.product([-1,1],repeat=len(a))]
  else:
   pooled=af+bf;distribution=[]
   for selection in itertools.combinations(range(len(pooled)),len(a)):
    chosen=set(selection);distribution.append(sum(x for i,x in enumerate(pooled) if i not in chosen)/len(b)-sum(pooled[i] for i in selection)/len(a))
  expected=min(Fraction(1),2*min(Fraction(sum(v<=observed for v in distribution),len(distribution)),Fraction(sum(v>=observed for v in distribution),len(distribution))))
  options=ExperimentRequest(run_id='oracle',conditions=['a','b'],design='paired_experiments' if paired else 'independent_experiments',metric='mean',iterations=199,seed=1729)
  actual=analyze_experiment(run_record(a,b,paired),options)['contrasts'][0]
  assert actual['permutation_exact'] and math.isclose(actual['permutation_p_two_sided'],float(expected),abs_tol=1e-12)
  cases.append({'paired':paired,'a':a,'b':b,'assignments':len(distribution),'rational_oracle_p':str(expected),'engine_p':actual['permutation_p_two_sided'],'agreed':True})
 return cases

def posterior_check():
 values=np.array([-.4,.2,.7,1.2,1.7]);options=ExperimentRequest(run_id='oracle',conditions=['a','b'],design='independent_experiments',metric='mean',prior_mean=.5,prior_kappa=.3,prior_alpha=2.5,prior_beta=1.1)
 rng=np.random.default_rng(20261018);n=1_000_000
 # Draw only from the specified prior and weight by the original Gaussian data likelihood.
 variance=options.prior_beta/rng.gamma(options.prior_alpha,size=n)
 mu=rng.normal(options.prior_mean,np.sqrt(variance/options.prior_kappa))
 logweight=-len(values)*np.log(variance)/2-sum((value-mu)**2 for value in values)/(2*variance)
 weight=np.exp(logweight-logsumexp(logweight));ess=float(1/np.sum(weight**2));mean=float(np.dot(weight,mu))
 order=np.argsort(mu);quantiles=np.interp([.025,.975],np.cumsum(weight[order]),mu[order])
 actual=normal_posterior(values,options)
 assert ess>10000 and abs(mean-actual['posterior_mean'])<.02
 assert np.max(np.abs(quantiles-actual['credible_interval_95']))<.025
 return {'method':'Prior importance sampling with original Gaussian likelihood; independent of closed-form posterior updates','seed':20261018,'prior_draws':n,'effective_sample_size':ess,'importance_posterior_mean':mean,'closed_form_mean':actual['posterior_mean'],'importance_ci95':quantiles.tolist(),'closed_form_ci95':actual['credible_interval_95'],'comparison_tolerances':{'mean_absolute':.02,'interval_endpoint_absolute':.025},'agreed_within_mc_tolerance':True,'scope':'One prior/dataset. Monte Carlo agreement is not frequentist coverage or proof of a binding-specific model.'}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 report={'exact_permutations':exact_checks(),'bayesian_posterior':posterior_check(),'scope':'Developer-run mathematical cross-checks using separate enumeration/integration implementations; no independent human review or biological certification.'};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
