"""Descriptive batch design checks; never infer independence from names alone."""
from collections import defaultdict


def summarize_design(items):
    groups = defaultdict(lambda: {'images': 0, 'experiments': set(), 'cells': set(), 'missing_labels': 0})
    sources = defaultdict(list)
    for item in items:
        condition = item.get('condition', '').strip()
        experiment = item.get('experiment', '').strip()
        cell = item.get('cell', '').strip()
        group = groups[condition]
        group['images'] += 1
        if experiment: group['experiments'].add(experiment)
        if experiment and cell: group['cells'].add((experiment, cell))
        if not all((condition, experiment, cell)): group['missing_labels'] += 1
        digest = item.get('image', {}).get('sha256')
        if digest: sources[digest].append(item)
    repeated = []
    for digest, entries in sources.items():
        if len(entries) < 2: continue
        repeated.append({'source_sha256': digest, 'image_ids': [i['image_id'] for i in entries],
                         'conflicting_experiments_or_conditions': len({(i.get('condition', '').strip(), i.get('experiment', '').strip()) for i in entries}) > 1})
    return {'algorithm': 'batch-design-review-1', 'groups': [
        {'condition': condition, 'images': g['images'], 'labelled_experiments': len(g['experiments']),
         'labelled_cells': len(g['cells']), 'images_missing_design_labels': g['missing_labels']}
        for condition, g in sorted(groups.items())], 'repeated_sources': repeated,
        'scope': 'Counts reflect supplied labels, not verified experimental independence. Missing labels do not prevent descriptive image measurement. Identical raw sources cannot represent independent experiments or different conditions. Repeated ROIs and Z planes are not independent experiments.'}


def roi_geometry_key(roi,info):
    """Canonical exact geometry; ignore display IDs and polygon start/orientation."""
    import math
    points=roi.get('points',[])
    if roi.get('kind')=='circle' and len(points)==2:
        centre=(points[0]['x'],points[0]['y'])
        if roi.get('diameter_um') is not None:
            calibration=info.get('calibration',{})
            sx=calibration.get('X',{}).get('value_um');sy=calibration.get('Y',{}).get('value_um')
            if not sx or not sy:return None
            rx,ry=roi['diameter_um']/(2*sx),roi['diameter_um']/(2*sy)
        else:rx=ry=math.hypot(points[1]['x']-centre[0],points[1]['y']-centre[1])
        return ('circle',roi['z'],*centre,rx,ry)
    if roi.get('kind')=='polygon' and len(points)>=3:
        vertices=[(p['x'],p['y']) for p in points]
        def normalized(v):
            i=min(range(len(v)),key=v.__getitem__)
            return tuple(v[i:]+v[:i])
        return ('polygon',roi['z'],min(normalized(vertices),normalized(list(reversed(vertices)))))
    return None
