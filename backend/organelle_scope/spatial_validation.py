"""Explicit translation null model, independent numeric references, and sensitivity."""
import numpy as np
from pydantic import BaseModel, Field
from scipy.stats import pearsonr, spearmanr
from organelle_scope.roi_analysis import AreaROI, pair_metrics, pearson, roi_mask
from organelle_scope.processing import ProcessingConfig
from organelle_scope.image_io import ImageError


class SpatialRequest(BaseModel):
    roi: AreaROI
    channel_a: int = Field(default=0, ge=0, le=3)
    channel_b: int = Field(default=1, ge=0, le=3)
    iterations: int = Field(default=199, ge=19, le=999)
    seed: int = Field(default=1729, ge=0, le=2**32-1)
    acknowledge_stationarity: bool = False
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)


def spatial_shift(a, b, roi, iterations, seed, spacing=(None,None)):
    mask, warnings = roi_mask(roi, a.shape, spacing)
    yy, xx = np.nonzero(mask)
    if len(yy)*iterations > 25_000_000:
        raise ImageError("Choose a smaller ROI or fewer shifts (limit: 25 million pixel comparisons).")
    observed = pearson(a[mask], b[mask])
    if observed is None:
        raise ImageError("The observed correlation is undefined for a constant ROI channel.")
    h, w = a.shape
    total = h*w-1
    rng = np.random.default_rng(seed)
    # Enumerate all nonidentity translations when possible; otherwise sample uniformly with replacement.
    exact = total <= iterations
    codes = np.arange(1, total+1) if exact else rng.integers(1, total+1, size=iterations)
    scores = []
    for code in codes:
        dy, dx = divmod(int(code), w)
        score = pearson(a[mask], b[(yy+dy)%h, (xx+dx)%w])
        if score is None:
            raise ImageError("A translated ROI is constant. This null model is unsuitable; choose a different region/model.")
        scores.append(score)
    scores = np.asarray(scores)
    tail = int(np.count_nonzero(scores >= observed-1e-12))
    return {"model":"whole-plane toroidal translation of channel B; fixed XY ROI", "algorithm_version":"toroidal-1",
            "alternative":"greater (positive association)", "tie_tolerance":1e-12, "observed_pearson":observed,
            "tail_probability":(tail+1)/(len(scores)+1), "exceedances":tail,
            "iterations":len(scores), "seed":seed, "exhaustive":exact,
            "minimum_tail_probability":1/(len(scores)+1), "null_scores":scores.tolist(),
            "null_quantiles":np.quantile(scores,[.025,.5,.975]).tolist(), "pixel_count":len(yy),
            "warnings":warnings+["Assumes translation invariance across the entire XY field. Borders wrap; different compartments and gradients can invalidate this null.",
            "ROI selection must be independent of the observed association. This is one unadjusted test; repeated ROIs/channel tests require multiplicity control.",
            "A small tail probability is conditional on this spatial model, not a probability of binding or biological replication."]}


def reference_benchmarks():
    checks=[]
    rng=np.random.default_rng(1413)
    for maximum in (255,65535):
        a=rng.integers(0,maximum+1,512).astype(float)
        b=np.clip(.5*a+rng.normal(0,maximum*.2,512),0,maximum)
        actual=pair_metrics(a,b,'zero')
        for name, reference in [('pcc',float(pearsonr(a,b).statistic)),('spearman',float(spearmanr(a,b).statistic))]:
            error=abs(actual[name]-reference)
            checks.append({'case':f'{maximum+1}-level {name}','actual':actual[name],'reference':reference,'absolute_error':error,'passed':error<1e-10})
    result=pair_metrics(np.array([0,1,2,3]),np.array([0,2,4,6]),'manual',1,4)
    for name,expected in [('thresholded_m1',.5),('thresholded_m2',5/6)]:
        checks.append({'case':f'analytic {name}','actual':result[name],'reference':expected,'absolute_error':abs(result[name]-expected),'passed':abs(result[name]-expected)<1e-12})
    return {'algorithm_version':'reference-1','checks':checks,'passed':all(c['passed'] for c in checks),
            'reference':'SciPy pearsonr/spearmanr and hand-derived Manders examples',
            'fiji_benchmark_status':'pending independent Fiji comparison','biological_validation':'pending; not publication certification'}
