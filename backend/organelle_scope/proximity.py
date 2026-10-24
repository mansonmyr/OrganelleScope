# Copyright (c) 2026 Kai Hong Ooi
# SPDX-License-Identifier: GPL-3.0-only
"""Directed distances between foreground voxel centres in one calibrated cuboid."""
import numpy as np
from scipy.ndimage import distance_transform_edt


# Manuscript Section 5: both directed physical voxel-centre summaries.
def proximity_summary(marker, reference, spacing_zyx, threshold_um):
    marker, reference = np.asarray(marker, dtype=bool), np.asarray(reference, dtype=bool)
    if marker.ndim != 3 or marker.shape != reference.shape:
        raise ValueError('Proximity masks must have matching three-dimensional shapes.')
    spacing = np.asarray(spacing_zyx, dtype=float)
    if spacing.shape != (3,) or not np.isfinite(spacing).all() or np.any(spacing <= 0):
        raise ValueError('Proximity requires finite positive Z/Y/X spacing.')
    if not np.isfinite(threshold_um) or threshold_um <= 0:
        raise ValueError('Choose a finite positive proximity threshold.')
    marker_count, reference_count = int(marker.sum()), int(reference.sum())
    warnings=[]
    if marker.shape[0]>1 and threshold_um<spacing[0]:warnings.append('The near-distance cutoff is smaller than the Z step. Adjacent-plane voxel centres cannot fall within it; this is not an optical resolution claim.')
    if marker.shape[0]<5:warnings.append('This cuboid contains fewer than five Z planes. Coarse axial sampling limits structural interpretation.')
    boundary=np.zeros(marker.shape,dtype=bool)
    for axis in range(3):
        for index in (0,-1):
            selection=[slice(None)]*3;selection[axis]=index;boundary[tuple(selection)]=True
    marker_edge=int(np.count_nonzero(marker & boundary));reference_edge=int(np.count_nonzero(reference & boundary))
    if marker_edge or reference_edge:warnings.append('Foreground touches a cuboid face. Objects and the available reference search may be truncated.')
    shared = {
        'algorithm_version':'directed-centres-2-quality',
        'mask_occupancy':{'cuboid_voxels':int(marker.size),'marker_fraction':marker_count/marker.size if marker.size else 0,'reference_fraction':reference_count/marker.size if marker.size else 0},
        'sampling_review':{'z_step_um':float(spacing[0]),'z_planes':marker.shape[0],'cutoff_smaller_than_z_step':bool(marker.shape[0]>1 and threshold_um<spacing[0]),'marker_boundary_voxels':marker_edge,'reference_boundary_voxels':reference_edge},
        'quality_warnings':warnings,
        'marker_foreground_voxels': marker_count,
        'reference_foreground_voxels': reference_count,
        'overlapping_foreground_voxels': int(np.count_nonzero(marker & reference)),
        'spacing_zyx_um': spacing.tolist(),
        'distance_threshold_um': float(threshold_um),
        'reference_search_domain': 'Selected inclusive cuboid only; outside reference signal is not searched.',
        'definition': 'Directed nearest occupied voxel-centre Euclidean distances using Z/Y/X sampling. The fraction is P(distance <= threshold | source foreground voxel), with equal voxel weighting. It is not a molecule-to-molecule distance, intensity fraction, binding probability or significance test. Direction reversal changes the denominator. Registration, label offsets and optical resolution remain acquisition limitations.',
    }
    if not marker_count or not reference_count:
        return {**shared, 'unavailable_reason': 'Marker mask is empty.' if not marker_count else 'Reference mask is empty.'}

    def directed(source, target):
        values = distance_transform_edt(~target, sampling=spacing)[source]
        boundary = np.zeros(source.shape, dtype=bool)
        for axis in range(3):
            for index in (0, -1):
                selection = [slice(None)] * 3
                selection[axis] = index
                boundary[tuple(selection)] = True
        return {
            'source_voxels': int(source.sum()),
            'nearest_occupied_voxel_center_um': float(values.min()),
            'median_occupied_voxel_center_um': float(np.median(values)),
            'p95_occupied_voxel_center_um': float(np.percentile(values, 95)),
            'within_distance_voxels': int(np.count_nonzero(values <= threshold_um)),
            'fraction_within_distance': float(np.mean(values <= threshold_um)),
            'source_voxels_on_cuboid_boundary': int(np.count_nonzero(source & boundary)),
        }
    forward, reverse = directed(marker, reference), directed(reference, marker)
    if forward['fraction_within_distance']==1:warnings.append('Every marker voxel is near the reference mask. Containment and mask occupancy can produce a fraction of one without demonstrating biological association; no spatial null is evaluated here.')
    return {**shared, 'marker_to_reference': forward, 'reference_to_marker': reverse,
            # Retain existing export keys, with their original forward direction.
            'nearest_occupied_voxel_center_um': forward['nearest_occupied_voxel_center_um'],
            'median_occupied_voxel_center_um': forward['median_occupied_voxel_center_um'],
            'fraction_marker_voxels_within_distance': forward['fraction_within_distance']}
