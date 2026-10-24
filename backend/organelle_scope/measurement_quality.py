# Copyright (c) 2026 Kai Hong Ooi
# SPDX-License-Identifier: GPL-3.0-only
"""Quality diagnostics describe supplied raw values, not detector certification."""
import numpy as np


def ceiling_quality(values, ceiling=None):
    source=np.asarray(values)
    if ceiling is None and np.issubdtype(source.dtype,np.unsignedinteger):
        ceiling=int(np.iinfo(source.dtype).max)
    count=int(source.size)
    hits=int(np.count_nonzero(source>=ceiling)) if ceiling is not None else None
    return {'sample_count':count,'storage_ceiling':ceiling,'ceiling_samples':hits,
            'ceiling_fraction':hits/count if hits is not None and count else None,
            'scope':'Raw selected-region samples at the storage ceiling; not a detector saturation calibration. Absence of ceiling samples does not exclude clipping below that ceiling.'}


def background_quality(values):
    a=np.asarray(values,dtype=np.float64)
    return {'mean':float(a.mean()),'min':float(a.min()),'max':float(a.max()),'std':float(a.std()),'range':float(np.ptp(a))}
