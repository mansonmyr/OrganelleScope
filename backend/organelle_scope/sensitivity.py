"""One-factor-at-a-time geometry/threshold exploration; no optimal-setting selection."""
from pydantic import Field
from organelle_scope.roi_analysis import AnalysisRequest

class RoiSweepRequest(AnalysisRequest):
    threshold_step:float=Field(default=10,gt=0,allow_inf_nan=False)
    size_fraction:float=Field(default=.2,gt=0,le=.5,allow_inf_nan=False)


def scaled_roi(roi,factor):
    points=roi.points
    cx,cy=(points[0].x,points[0].y) if roi.kind=='circle' else (sum(p.x for p in points)/len(points),sum(p.y for p in points)/len(points))
    values=[p.model_copy(update={'x':cx+(p.x-cx)*factor,'y':cy+(p.y-cy)*factor}) for p in points]
    return roi.model_copy(update={'points':values,'diameter_um':roi.diameter_um*factor if roi.diameter_um else None})
