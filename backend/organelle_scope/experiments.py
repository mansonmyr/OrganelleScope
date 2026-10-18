"""Experiment/cell aggregation, clustered bootstrap and explicit Gaussian inference."""
from collections import defaultdict
from hashlib import sha256
from itertools import combinations
import json,math
import numpy as np
from scipy import stats
from fastapi import Depends,HTTPException
from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
from uuid import UUID
from organelle_scope.image_io import ImageError
from organelle_scope.batch_design import summarize_design

class ExperimentRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    run_id:str
    conditions:list[str]=Field(min_length=2,max_length=5)
    design:Literal['paired_experiments','independent_experiments']
    metric:Literal['pcc','spearman','m1','m2','thresholded_m1','thresholded_m2','mean']='pcc'
    channel_a:int=Field(default=0,ge=0,le=3)
    channel_b:int=Field(default=1,ge=0,le=3)
    scale:Literal['native','fisher_z']='native'
    iterations:int=Field(default=1999,ge=199,le=9999)
    seed:int=Field(default=1729,ge=0,le=2**32-2)
    normal_model:bool=False
    prior_mean:float=Field(default=0,allow_inf_nan=False)
    prior_kappa:float=Field(default=.01,gt=0,le=10000,allow_inf_nan=False)
    prior_alpha:float=Field(default=2,gt=1,le=10000,allow_inf_nan=False)
    prior_beta:float=Field(default=1,gt=0,le=1e12,allow_inf_nan=False)

def bh_adjust(values):
    order=np.argsort(values);result=np.empty(len(values));adjusted=np.minimum.accumulate((np.asarray(values)[order]*len(values)/np.arange(1,len(values)+1))[::-1])[::-1];result[order]=np.minimum(1,adjusted);return result.tolist()

def normal_posterior(values,options):
    data=np.asarray(values,dtype=float);n=len(data);mean=float(data.mean());k=options.prior_kappa+n;alpha=options.prior_alpha+n/2
    location=(options.prior_kappa*options.prior_mean+n*mean)/k
    beta=options.prior_beta+float(np.sum((data-mean)**2))/2+options.prior_kappa*n*(mean-options.prior_mean)**2/(2*k)
    scale=math.sqrt(beta/(alpha*k));interval=stats.t.interval(.95,df=2*alpha,loc=location,scale=scale)
    return {'posterior_mean':location,'credible_interval_95':list(map(float,interval)),'student_t_df':2*alpha,'student_t_scale':scale,'posterior_expected_sigma_squared':beta/(alpha-1),'posterior_variance_mu':beta/((alpha-1)*k),'prior':{'mu0':options.prior_mean,'kappa0':options.prior_kappa,'alpha0':options.prior_alpha,'beta0':options.prior_beta},'likelihood':'Independent experiment means ~ Normal(mu,sigma²). Normal-inverse-Gamma prior. Conditional on these assumptions; not a probability of binding/causality.'}

def analyze_experiment(run,options):
    if len(set(options.conditions))!=len(options.conditions):raise ImageError('Select distinct conditions.')
    if options.metric!='mean' and options.channel_a>=options.channel_b:raise ImageError('Choose channel A before channel B; Manders directions follow this order.')
    if options.scale=='fisher_z' and options.metric not in ('pcc','spearman'):raise ImageError('Fisher transformation applies only to correlation metrics.')
    design=summarize_design([i for i in run['items'] if i.get('condition') in options.conditions])
    if any(s['conflicting_experiments_or_conditions'] for s in design['repeated_sources']):raise ImageError('Identical raw source data were assigned to different conditions or experiments. Correct the batch design; copied files are not independent experiments.')
    by_cell=defaultdict(list);source_rows=[];excluded=[];recipes=set();channel_identities=set()
    for item in run['items']:
        if item.get('condition') not in options.conditions:continue
        if item['status']!='completed':raise ImageError('Every selected image must have completed measurements; failed/cancelled images are not silently excluded.')
        condition=item['condition'];experiment=item.get('experiment','').strip();cell=item.get('cell','').strip()
        if not experiment or not cell:raise ImageError('Every selected image needs an independent experiment ID and a cell ID in the batch.')
        result=item['result'];request=result['request']
        signature={'threshold_mode':request['threshold_mode'],'thresholds':request.get('thresholds',[]),'processing':request.get('processing',{})}
        if signature['processing'].get('restoration_result_id') or result['processing'].get('denoising') or result['processing'].get('deconvolution'):
            raise ImageError('This batch used retired denoising/deconvolution. Recalculate the images with supported processing before new inference; the historical batch is preserved.')
        recipes.add(json.dumps(signature,sort_keys=True))
        labels=result.get('image_info',{}).get('channel_labels',[])
        selected=[options.channel_a] if options.metric=='mean' else [options.channel_a,options.channel_b]
        if any(c>=len(labels) or not isinstance(labels[c],str) or not labels[c].strip() for c in selected):raise ImageError('Selected channel identities are missing. Assign marker names and recalculate the batch before comparing conditions.')
        channel_identities.add(tuple(labels[c] for c in selected))
        for row in result['results']:
            if options.metric=='mean':
                target=next((c for c in row['channel_summary'] if c['channel']==options.channel_a),None);value=target.get('mean') if target else None
            else:
                target=next((p for p in row['pairs'] if p['channel_a']==options.channel_a and p['channel_b']==options.channel_b),None);value=target.get(options.metric) if target else None
            if value is None or not np.isfinite(value):raise ImageError('A selected measurement is undefined or its channel is missing. Resolve it before experiment inference.')
            if options.scale=='fisher_z':
                if abs(value)>=1:raise ImageError('Fisher z is undefined at ±1. Use native descriptive inference or review the perfect correlation; no clipping is substituted.')
                value=float(np.arctanh(value))
            by_cell[(condition,experiment,cell)].append(value);source_rows.append({'image_id':item['image_id'],'source_sha256':result['source_sha256'],'roi_id':row['roi']['id'],'condition':condition,'experiment':experiment,'cell':cell,'value':value})
    if len(channel_identities)>1:raise ImageError('Selected channel names differ across images. Match biological markers in the same stored channel order before comparing conditions.')
    if len(recipes)!=1:raise ImageError('Selected images use different processing/threshold conventions. Create a matched batch before comparison.')
    groups={condition:defaultdict(list) for condition in options.conditions}
    for (condition,experiment,cell),values in by_cell.items():groups[condition][experiment].append(float(np.mean(values)))
    if any(len(experiments)<3 for experiments in groups.values()):raise ImageError('This workflow requires at least three independent experiments per condition. More cells do not replace independent experiments.')
    if len(source_rows)>50000 or any(len(g)>100 for g in groups.values()):raise ImageError('The current inference budget is 50,000 ROI values and 100 experiments per condition.')
    estimated_cell_draws=options.iterations*(len(options.conditions)-1)*sum(len(g)*max(map(len,g.values())) for g in groups.values())
    if estimated_cell_draws>20_000_000:raise ImageError('This comparison exceeds the 20 million resampled-cell work budget. Reduce conditions, cells or bootstrap iterations; no cells are silently dropped.')
    rng=np.random.default_rng(options.seed);summary=[]
    for name,experiments in groups.items():
        values=np.asarray([np.mean(v) for v in experiments.values()]);item={'condition':name,'independent_experiments':len(experiments),'cells':sum(len(v) for v in experiments.values()),'mean':float(values.mean()),'experiment_means':dict(zip(experiments,map(float,values))),'normal_mle_mean':float(values.mean()) if options.normal_model else None,'normal_mle_sigma':float(values.std(ddof=0)) if options.normal_model else None}
        if options.normal_model:
            if options.metric in ('m1','m2','thresholded_m1','thresholded_m2') or options.metric in ('pcc','spearman') and options.scale!='fisher_z':raise ImageError('The Gaussian Bayesian model is offered for intensity means or Fisher-transformed correlations; use bootstrap summaries for bounded fractions/native correlations.')
            item['normal_posterior']=normal_posterior(values,options)
            item['prior_sensitivity']=[{'variance_scale_factor':factor,'posterior':normal_posterior(values,options.model_copy(update={'prior_beta':options.prior_beta*factor}))} for factor in (.1,10)]
            item['model_diagnostics']={'experiment_means':values.tolist(),'shapiro_p_descriptive':float(stats.shapiro(values).pvalue) if len(values)>=3 and np.ptp(values)>0 else None,'scope':'Inspect experiment means, outliers and variance assumptions. A nonsignificant normality test does not establish normality. Bayesian credible intervals do not promise 95% repeated-sampling coverage; prior sensitivity can be substantial with few experiments.'}
        summary.append(item)
    contrasts=[]
    for a,b in combinations(options.conditions,2):
        ga,gb=groups[a],groups[b];ka,kb=list(ga),list(gb)
        paired=options.design=='paired_experiments'
        if paired and set(ka)!=set(kb):raise ImageError('Paired conditions must have exactly matching experiment IDs. Unmatched experiments are not dropped.')
        if not paired and set(ka)&set(kb):raise ImageError('Independent conditions must use distinct experiment IDs. For matched experiments choose the paired design.')
        va=np.asarray([np.mean(ga[k]) for k in ka]);vb=np.asarray([np.mean(gb[k]) for k in (ka if paired else kb)])
        draws=[]
        for _ in range(options.iterations):
            ia=rng.integers(len(ka),size=len(ka));ib=ia if paired else rng.integers(len(kb),size=len(kb))
            def sample(g,keys,indices):return np.mean([np.mean(rng.choice(g[keys[i]],size=len(g[keys[i]]),replace=True)) for i in indices])
            draws.append(float(sample(gb,ka if paired else kb,ib)-sample(ga,ka,ia)))
        difference=float(vb.mean()-va.mean())
        permutation=stats.permutation_test((va,vb),lambda x,y:np.mean(y)-np.mean(x),permutation_type='samples' if paired else 'independent',n_resamples=options.iterations,alternative='two-sided',rng=np.random.default_rng(options.seed+1),vectorized=False)
        assignments=2**len(va) if paired else math.comb(len(va)+len(vb),len(va))
        contrasts.append({'permutation_assignments_possible':assignments,'permutation_exact':assignments<=options.iterations,'minimum_attainable_two_sided_p':min(1.,2/(assignments if assignments<=options.iterations else options.iterations+1)),'condition_a':a,'condition_b':b,'difference_b_minus_a':difference,'hierarchical_bootstrap_ci95':list(map(float,np.quantile(draws,[.025,.975]))),'permutation_p_two_sided':float(permutation.pvalue),'bootstrap_replicates':options.iterations,'experimental_units':len(va) if paired else len(va)+len(vb)})
    for contrast,q in zip(contrasts,bh_adjust([c['permutation_p_two_sided'] for c in contrasts])):contrast['bh_adjusted_p_within_report']=q
    return {'selected_channel_labels':list(next(iter(channel_identities))),'algorithm':'experiment-inference-2','request':options.model_dump(),'groups':summary,'contrasts':contrasts,'source_rows':source_rows,'batch_run_id':run['id'],'batch_run_sha256':sha256(json.dumps(run,sort_keys=True).encode()).hexdigest(),'aggregation':'Average ROIs within each (condition, experiment, cell); average cells within experiment; weight independent experiments equally. Bootstrap resamples experiments then cells; paired resampling preserves experiment pairing. No pixels are independent replicates.','multiple_comparisons':'Benjamini-Hochberg adjustment over all contrasts in this report for this one metric. Other metrics/reports are not part of this family.','scope':'Measured condition association under the selected design and resampling assumptions. No causal knockdown claim, molecular binding probability or biological validation certificate.'}

def register_experiments(app,data_dir,authorized):
    @app.post('/api/experiments/analyze',dependencies=[Depends(authorized)])
    def analyze(options:ExperimentRequest):
        try:
            UUID(options.run_id);p=data_dir/'batch-data'/'runs'/(options.run_id+'.json')
            if not p.is_file():raise ImageError('Completed batch run not found.')
            run=json.loads(p.read_text())
            if run['status'] in ('running','cancelling'):raise ImageError('Wait for the batch to finish.')
            return analyze_experiment(run,options)
        except (ImageError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc
