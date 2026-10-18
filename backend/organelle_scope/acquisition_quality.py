"""Exact selected-plane acquisition diagnostics; never infer detector bit depth."""
import numpy as np


def plane_quality(plane, channel, label, detector_ceiling=None):
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
    if detector_ceiling is not None and (detector_ceiling<1 or detector_ceiling>ceiling):raise ValueError('Declared detector ceiling must be within the stored intensity range.')
    if detector_ceiling is not None and high>detector_ceiling:notes.append('Observed values exceed the declared detector ceiling; verify this setting and any acquisition/export scaling.')
    if detector_ceiling is not None and np.any(plane>=detector_ceiling):notes.append('Pixels reach or exceed the user-declared detector ceiling; inspect possible clipping. This is not proof of saturation.')
    return {'observed_max_pixels':int(np.count_nonzero(plane==high)),'declared_detector_ceiling':detector_ceiling,'at_or_above_declared_ceiling_pixels':int(np.count_nonzero(plane>=detector_ceiling)) if detector_ceiling is not None else None,'channel': channel, 'label': label, 'pixel_count': int(plane.size), 'min': low, 'max': high,
            'mean': float(plane.mean(dtype=np.float64)), 'std': float(plane.std(dtype=np.float64)),
            'zero_pixels': zeros, 'storage_ceiling': ceiling, 'storage_ceiling_pixels': clipped,
            'storage_ceiling_fraction': clipped/plane.size, 'detector_saturation': 'not determined', 'notes': notes}


def sampling_review(info,lateral_resolution_um=None,axial_resolution_um=None):
    rows=[]
    for axis in 'XYZ':
        calibration=info.calibration[axis];spacing=calibration.value_um
        resolution=axial_resolution_um if axis=='Z' else lateral_resolution_um
        relevant=axis!='Z' or info.dimensions['Z']>1
        if not relevant:status='Not applicable to a single plane.'
        elif spacing is None or not np.isfinite(spacing) or spacing<=0 or calibration.conflict:status='Sampling unknown or conflicting; resolve calibration.'
        elif resolution is None:status='Resolution not supplied; sampling adequacy is unassessed.'
        elif spacing>resolution/2:status='Coarser than half the supplied resolution; review undersampling.'
        else:status='At least two samples per supplied resolution; screening criterion only.'
        rows.append({'axis':axis,'spacing_um':spacing,'calibration_source':calibration.source,'calibration_conflict':calibration.conflict,'declared_resolution_um':resolution,'samples_per_declared_resolution':resolution/spacing if relevant and resolution is not None and spacing is not None and np.isfinite(spacing) and spacing>0 and not calibration.conflict else None,'status':status})
    return {'axes':rows,'resolution_source':'Optional user-supplied nominal resolution, not inferred from pixel spacing.','registration':'Not measured. No displacement correction or registration accuracy is inferred without calibration/control images.','scope':'Two samples per declared resolution is a screening comparison, not proof of Nyquist adequacy or measured optical performance. Resolution definitions, PSF shape, confocal settings, refractive index and acquisition conditions matter.'}
