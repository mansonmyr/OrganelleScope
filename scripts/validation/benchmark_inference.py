"""Seeded calibration of the implemented Gaussian posterior under its stated model."""
import json
from pathlib import Path
import numpy as np
from organelle_scope.experiments import normal_posterior,ExperimentRequest
r=np.random.default_rng(20261017);out=[]
for n in [5,20,50]:
    for mu,sigma in [(0,1),(2,2)]:
        o=ExperimentRequest(run_id='synthetic',conditions=['a','b'],design='independent_experiments',normal_model=True,metric='mean',prior_mean=0,prior_kappa=.01,prior_alpha=2,prior_beta=1)
        covered=0;biased=0
        for _ in range(1000):
            p=normal_posterior(r.normal(mu,sigma,n),o);lo,hi=p['credible_interval_95'];covered+=lo<=mu<=hi;biased+=p['posterior_mean']-mu
        out.append({'experiments':n,'true_mean':mu,'true_sigma':sigma,'coverage_fraction':covered/1000,'mean_posterior_bias':biased/1000})
report={'seed':20261017,'simulations_per_case':1000,'prior':o.model_dump(include={'prior_mean','prior_kappa','prior_alpha','prior_beta'}),'cases':out,'scope':'Gaussian experiment means with known simulated truth. Coverage is conditional on this model and prior; no biological or non-Gaussian guarantee. Small-n prior sensitivity is expected. Not a calibration of hierarchical bootstrap intervals.'}
Path('docs/INFERENCE_SYNTHETIC_BENCHMARK.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
