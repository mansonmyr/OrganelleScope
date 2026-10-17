"""Per-plane ROI measurements on native intensities, with explicit undefined cases.

No pixel-i.i.d. significance or biological interaction probability is inferred.
Thresholded Manders here uses a strict opposite-channel `>` comparison and a
whole-ROI intensity denominator. Costes-style automatic thresholds use positive
orthogonal regression and the union of pixels below either paired threshold.
"""
from __future__ import annotations

import math
from itertools import combinations
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field, model_validator
from scipy.stats import rankdata

from organelle_scope.image_io import ImageError
from organelle_scope.processing import ProcessingConfig


class Point(BaseModel):
    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)


class AreaROI(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    kind: Literal["circle", "polygon"]
    z: int = Field(ge=0)
    points: list[Point] = Field(min_length=2, max_length=512)
    diameter_um: float | None = Field(default=None,gt=0,allow_inf_nan=False)

    @model_validator(mode='after')
    def physical_circle_only(self):
        if self.diameter_um is not None and self.kind!='circle':
            raise ValueError('A physical diameter applies only to circular ROIs.')
        return self


class AnalysisRequest(BaseModel):
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    rois: list[AreaROI] = Field(min_length=1, max_length=100)
    target_channel: int = Field(default=0, ge=0, le=3)
    threshold_mode: Literal["zero", "manual", "costes"] = "costes"
    thresholds: list[float] = Field(default_factory=list)


def _cross(a, b, c):
    return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)


def _intersects(a, b, c, d):
    if max(a.x, b.x) < min(c.x, d.x) or max(c.x, d.x) < min(a.x, b.x) or max(a.y, b.y) < min(c.y, d.y) or max(c.y, d.y) < min(a.y, b.y):
        return False
    return _cross(a,b,c)*_cross(a,b,d) <= 0 and _cross(c,d,a)*_cross(c,d,b) <= 0


def roi_mask(roi: AreaROI, shape: tuple[int, int], spacing=(None,None)) -> tuple[np.ndarray, list[str]]:
    h, w = shape
    points = roi.points
    if any(p.x < 0 or p.y < 0 or p.x > w-1 or p.y > h-1 for p in (points[:1] if roi.diameter_um is not None else points)):
        raise ImageError("ROI points must lie within the image pixel-center coordinates.")
    yy, xx = np.ogrid[:h, :w]
    warnings = []
    if roi.kind == "circle":
        if len(points) != 2:
            raise ImageError("A circular ROI needs a center and an edge point.")
        a, b = points
        if roi.diameter_um is not None:
            sx,sy=spacing
            if sx is None or sy is None or not all(math.isfinite(v) and v>0 for v in (sx,sy)):
                raise ImageError('A diameter in micrometers requires valid X and Y calibration.')
            rx,ry=roi.diameter_um/(2*sx),roi.diameter_um/(2*sy)
        else:
            rx=ry=math.hypot(b.x-a.x,b.y-a.y)
        if rx <= 0 or ry <= 0:
            raise ImageError("Draw a circle with a nonzero radius.")
        mask = (((xx-a.x)/rx)**2+((yy-a.y)/ry)**2 <= 1+1e-12) if roi.diameter_um is not None else ((xx-a.x)**2+(yy-a.y)**2 <= rx**2)
        if a.x-rx < 0 or a.y-ry < 0 or a.x+rx > w-1 or a.y+ry > h-1:
            warnings.append("The circle extends outside the image; measurements use its intersection with the image.")
    else:
        if len(points) < 3:
            raise ImageError("A polygon needs at least three vertices.")
        if len({(p.x,p.y) for p in points}) != len(points):
            raise ImageError("Polygon vertices must be distinct; do not repeat the first vertex.")
        edges = list(zip(points, points[1:]+points[:1]))
        for i, j in combinations(range(len(edges)), 2):
            if j == i+1 or (i == 0 and j == len(edges)-1):
                continue
            if _intersects(*edges[i], *edges[j]):
                raise ImageError("Self-intersecting polygons are not supported. Redraw the boundary.")
        if abs(sum(a.x*b.y-b.x*a.y for a,b in edges)) < 1e-9:
            raise ImageError("Polygon area must be nonzero.")
        inside = np.zeros(shape, bool)
        boundary = np.zeros(shape, bool)
        for a, b in edges:
            if a.y != b.y:
                crossing = ((a.y > yy) != (b.y > yy)) & (xx < (b.x-a.x)*(yy-a.y)/(b.y-a.y)+a.x)
                inside ^= crossing
            cross = (b.x-a.x)*(yy-a.y)-(b.y-a.y)*(xx-a.x)
            boundary |= (np.abs(cross) < 1e-8) & (xx >= min(a.x,b.x)) & (xx <= max(a.x,b.x)) & (yy >= min(a.y,b.y)) & (yy <= max(a.y,b.y))
        mask = inside | boundary
    if mask.sum() < 3:
        raise ImageError("The ROI must contain at least three pixel centers.")
    return mask, warnings


def pearson(a: np.ndarray, b: np.ndarray) -> float | None:
    x = a.astype(np.float64) - np.mean(a, dtype=np.float64)
    y = b.astype(np.float64) - np.mean(b, dtype=np.float64)
    denom = float(np.linalg.norm(x)*np.linalg.norm(y))
    return float(np.clip(np.dot(x,y)/denom, -1, 1)) if denom > 0 else None


def automatic_thresholds(a: np.ndarray, b: np.ndarray) -> dict:
    """Native-integer Costes-style search, no mean-threshold fallback.

    Histogram cumulative moments evaluate all integer working thresholds in
    O(N + intensity range), instead of repeatedly scanning the whole ROI.
    The secondary threshold is continuous (no Fiji-specific integer rounding).
    """
    a = a.astype(np.float64); b = b.astype(np.float64)
    x = a-a.mean(); y = b-b.mean()
    va, vb, cov = float(np.dot(x,x)), float(np.dot(y,y)), float(np.dot(x,y))
    if va == 0 or vb == 0 or cov <= 0:
        return {"status": "not_applicable", "a": None, "b": None, "background_pcc": None}
    slope = (vb-va+math.sqrt((vb-va)**2+4*cov*cov))/(2*cov)
    intercept = float(b.mean()-slope*a.mean())
    swapped = slope > 1
    main, other = (b,a) if swapped else (a,b)
    m, offset = (1/slope, -intercept/slope) if swapped else (slope,intercept)
    activation = np.minimum(main, (other-offset)/m)
    bins = np.clip(np.ceil(activation), 0, int(main.max())).astype(np.int64)
    size = int(main.max())+1
    # Centering before accumulation avoids cancellation for large intensity offsets.
    u, v = main-main.mean(), other-other.mean()
    hist = lambda weights=None: np.cumsum(np.bincount(bins, weights=weights, minlength=size))
    n, su, sv, suu, svv, suv = hist(), hist(u), hist(v), hist(u*u), hist(v*v), hist(u*v)
    safe_n = np.maximum(n,1)
    v1, v2 = suu-su*su/safe_n, svv-sv*sv/safe_n
    valid = (n >= 3) & (v1 > 1e-9) & (v2 > 1e-9)
    r = np.full(size, np.nan)
    r[valid] = (suv[valid]-su[valid]*sv[valid]/n[valid])/np.sqrt(v1[valid]*v2[valid])
    indices = np.flatnonzero(valid & (r <= 0) & (m*np.arange(size)+offset >= 0))
    if not len(indices):
        return {"status": "not_found", "a": None, "b": None, "background_pcc": None}
    threshold = int(indices[-1])
    t1, t2 = float(threshold), float(m*threshold+offset)
    return {"status": "found", "a": t2 if swapped else t1, "b": t1 if swapped else t2,
            "background_pcc": float(r[threshold])}


def pair_metrics(a: np.ndarray, b: np.ndarray, mode: str, ta: float = 0, tb: float = 0) -> dict:
    a = a.astype(np.float64); b = b.astype(np.float64)
    pcc = pearson(a,b)
    spearman = pearson(rankdata(a),rankdata(b)) if pcc is not None else None
    norm = float(np.linalg.norm(a)*np.linalg.norm(b))
    total_a, total_b = float(a.sum()), float(b.sum())
    def manders(t1, t2):
        return (float(a[b > t2].sum()/total_a) if total_a else None,
                float(b[a > t1].sum()/total_b) if total_b else None)
    raw_m1, raw_m2 = manders(0,0)
    threshold = automatic_thresholds(a,b) if mode == "costes" else {"status": "provided", "a":ta, "b":tb, "background_pcc":None}
    m1, m2 = manders(threshold["a"], threshold["b"]) if threshold["a"] is not None else (None,None)
    warnings = []
    reasons = {}
    constant=[]
    for label,values in (('A',a),('B',b)):
        if np.std(values)==0:constant.append('channel '+label+(' contains only zero intensities' if not np.any(values) else ' has constant intensity'))
    if pcc is None:
        reasons['pcc']=reasons['spearman']='Correlation is undefined: '+('; '.join(constant) or 'insufficient variation')+' in the selected region. The normalization denominator is zero; unavailable is not a correlation of zero.'
    if not norm:reasons['moc']='Overlap is undefined because at least one channel has zero intensity energy in this region.'
    if not total_a:reasons['m1']='M1 is undefined because the summed intensity in channel A is zero (zero denominator).'
    if not total_b:reasons['m2']='M2 is undefined because the summed intensity in channel B is zero (zero denominator).'
    if threshold['a'] is None:
        reasons['thresholded_m1']=reasons['thresholded_m2']='Automatic thresholds were not obtained ('+threshold['status']+'). No fallback threshold is substituted.'
    else:
        if not total_a:reasons['thresholded_m1']=reasons['m1']
        if not total_b:reasons['thresholded_m2']=reasons['m2']
    if pcc is None:
        warnings.append("Correlation is undefined because at least one channel is constant in the selected region.")
    if threshold["a"] is None:
        warnings.append("Automatic thresholds were not obtained. Thresholded Manders is unavailable; no fallback threshold was substituted.")
    gaussian_lrt = None
    if pcc is not None and abs(pcc) < 1-1e-12:
        gaussian_lrt = float(-len(a)*math.log1p(-pcc*pcc))
    if gaussian_lrt is None:
        reasons['gaussian_lrt_statistic']='The Gaussian covariance statistic is unavailable for constant channels or a singular, perfectly correlated covariance model.'
    return {"unavailable_reasons":reasons,"pcc":pcc, "spearman":spearman, "moc":float(np.dot(a,b)/norm) if norm else None,
            "m1":raw_m1, "m2":raw_m2, "thresholded_m1":m1, "thresholded_m2":m2,
            "thresholds":threshold, "gaussian_lrt_statistic":gaussian_lrt,
            "gaussian_lrt_note":"Descriptive Gaussian likelihood ratio only; no calibrated p-value or probability of interaction. Spatial dependence is not modeled.",
            "warnings":warnings}


def regression(channels: list[np.ndarray], target: int, labels: list[str]) -> dict:
    y = channels[target].astype(np.float64)
    candidates = [i for i in range(len(channels)) if i != target]
    base = {"target_channel":target, "r_squared":None, "betas":[], "coefficient_ratio":None, "warnings":[]}
    if np.std(y) == 0 or len(y) <= len(candidates)+1:
        base["warnings"].append("Regression is undefined for a constant target or insufficient pixels.")
        return base
    active = [i for i in candidates if np.std(channels[i]) > 0]
    if not active:
        base["warnings"].append("All candidate channels are constant within this ROI.")
        return base
    X = np.column_stack([(channels[i]-np.mean(channels[i]))/np.std(channels[i]) for i in active])
    ys = (y-y.mean())/y.std()
    beta, _, rank, singular = np.linalg.lstsq(X,ys,rcond=None)
    r2 = float(np.clip(1-np.sum((ys-X@beta)**2)/np.sum(ys**2),0,1))
    base["r_squared"] = r2
    identifiable = rank == len(active) and singular[0]/singular[-1] < 1e6
    if not identifiable:
        base["warnings"].append("Candidate channels are collinear: individual coefficients and their ratio are not reliably identifiable.")
    if len(active) < len(candidates):
        base["warnings"].append("Constant candidate channels were excluded from regression.")
    base["betas"] = [{"channel":i, "label":labels[i], "value":float(beta[active.index(i)]) if i in active and identifiable else None} for i in candidates]
    magnitudes = sorted(np.abs(beta), reverse=True)
    if identifiable and len(magnitudes) > 1 and magnitudes[1] > 1e-10:
        base["coefficient_ratio"] = float(magnitudes[0]/magnitudes[1])
    base["warnings"].append("Standardized coefficients describe intensity associations, not molecular binding or causal effects.")
    return base


def analyze_roi(channels: list[np.ndarray], roi: AreaROI, labels: list[str], target: int,
                mode: str, thresholds: list[float], spacing: tuple[float | None, float | None]) -> dict:
    mask, warnings = roi_mask(roi, channels[0].shape, spacing)
    values = [c[mask].astype(np.float64) for c in channels]
    count = int(mask.sum())
    sx, sy = spacing
    pairs = []
    for i,j in combinations(range(len(channels)),2):
        pairs.append({"channel_a":i,"channel_b":j,"label_a":labels[i],"label_b":labels[j],
                      **pair_metrics(values[i],values[j],mode,thresholds[i],thresholds[j])})
    return {"roi":roi.model_dump(), "pixel_count":count,
            "area_um2":count*sx*sy if sx is not None and sy is not None else None,
            "channel_summary":[{"channel":i,"label":labels[i],"mean":float(v.mean()),"sum":float(v.sum()),"std":float(v.std())} for i,v in enumerate(values)],
            "pairs":pairs, "regression":regression(values,target,labels), "warnings":warnings}
