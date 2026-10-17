"""Exact selected-plane acquisition diagnostics; never infer detector bit depth."""
import numpy as np


def plane_quality(plane, channel, label):
    ceiling = int(np.iinfo(plane.dtype).max)
    low, high = int(plane.min()), int(plane.max())
    zeros = int(np.count_nonzero(plane == 0))
    clipped = int(np.count_nonzero(plane == ceiling))
    notes = []
    if high == 0:
        notes.append('All pixels are zero; correlations are undefined. This does not establish biological absence.')
    elif low == high:
        notes.append('Constant intensity; Pearson and Spearman are undefined.')
    if clipped:
        notes.append('Pixels reach the storage ceiling; review possible clipping in the acquisition settings.')
    return {'channel': channel, 'label': label, 'pixel_count': int(plane.size), 'min': low, 'max': high,
            'mean': float(plane.mean(dtype=np.float64)), 'std': float(plane.std(dtype=np.float64)),
            'zero_pixels': zeros, 'storage_ceiling': ceiling, 'storage_ceiling_pixels': clipped,
            'storage_ceiling_fraction': clipped/plane.size, 'detector_saturation': 'not determined', 'notes': notes}
