"""Full-resolution cuboid summaries, independent from downsampled VTK rendering."""
from itertools import combinations
import numpy as np
from pydantic import BaseModel, Field
from organelle_scope.processing import ProcessingConfig
from organelle_scope.roi_analysis import pair_metrics
from organelle_scope.image_io import ImageError
from organelle_scope.measurement_quality import ceiling_quality


class CuboidRequest(BaseModel):
    x0: int = Field(ge=0)
    x1: int = Field(ge=0)
    y0: int = Field(ge=0)
    y1: int = Field(ge=0)
    z0: int = Field(ge=0)
    z1: int = Field(ge=0)
    thresholds: list[float] = Field(default_factory=list, max_length=4)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)

    def validate_bounds(self, dimensions):
        for a in 'xyz':
            if getattr(self,a+'0')>getattr(self,a+'1') or getattr(self,a+'1')>=dimensions[a.upper()]:
                raise ImageError("Cuboid bounds must be ordered and inside the source image (inclusive pixel/slice indices).")
        count=(self.x1-self.x0+1)*(self.y1-self.y0+1)*(self.z1-self.z0+1)
        if count<3 or count>500_000:
            raise ImageError("Select a cuboid containing 3–500,000 source voxels for full-resolution measurements.")
        return count


def summarize_cuboid(values, labels, thresholds, spacing, raw_values=None, intensity_ceiling=None):
    count=len(values[0])
    volume=count*float(np.prod(spacing)) if all(v is not None for v in spacing) else None
    return {'voxel_count':count,'region_volume_um3':volume,
            'channels':[{'channel':i,'label':labels[i],'mean':float(a.mean()),'sum':float(a.sum(dtype=np.float64)),
            'std':float(a.std(dtype=np.float64)), 'raw_quality':ceiling_quality((raw_values if raw_values is not None else values)[i],intensity_ceiling),'above_threshold_voxels':int(np.count_nonzero(a>thresholds[i]))} for i,a in enumerate(values)],
            'pairs':[{'channel_a':i,'channel_b':j,'label_a':labels[i],'label_b':labels[j],
            **pair_metrics(values[i],values[j],'manual',thresholds[i],thresholds[j])} for i,j in combinations(range(len(values)),2)],
            'scope':'Full-resolution inclusive cuboid, not a segmented organelle volume. No voxel-independent significance or interaction inference.'}
