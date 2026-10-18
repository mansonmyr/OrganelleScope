"""Portable, escaped HTML report; embedded native-range previews and engine records."""
import base64
import hashlib
from html import escape
from io import BytesIO
import json
from datetime import datetime, timezone

import numpy as np
from PIL import Image
from fastapi import Depends, HTTPException
from fastapi.responses import HTMLResponse
from organelle_scope import __version__
from organelle_scope.assistant import WorkspaceContext
from organelle_scope.image_io import read_plane
from organelle_scope.interpretation import interpretation_snapshot


def text(value):
    return escape('Unavailable' if value is None else str(value),quote=True)


def details(title,value):
    return '<details><summary>'+text(title)+'</summary><pre>'+text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False))+'</pre></details>'


def build_review(record,folder):
    from organelle_scope.image_io import ImageInfo
    image=record['image'];info=ImageInfo.model_validate(image['info']);core=record['state'].get('core',{})
    analysis=core.get('analysis')
    matched=isinstance(analysis,dict) and analysis.get('source_sha256')==image['sha256'] and analysis.get('image_info')==image['info'] and analysis.get('request',{}).get('rois')==core.get('areas')
    request=(analysis or {}).get('request',{})
    if 'thresholdMode' in core:matched=matched and core['thresholdMode']==request.get('threshold_mode')
    if core.get('thresholdMode')=='manual':matched=matched and core.get('thresholds',[])[:info.dimensions['C']]==request.get('thresholds')
    if 'target' in core:matched=matched and core['target']==request.get('target_channel')
    saved=folder/'analysis.json'
    matched=matched and saved.is_file() and json.loads(saved.read_text())==analysis
    if not matched:analysis=None
    filtered={**record,'state':{**record['state'],'core':{**core,'analysis':analysis}}}
    reading=interpretation_snapshot(filtered)
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>OrganelleScope analysis review</title><style>body{font:15px system-ui;color:#173b48;background:#fdf0d5;margin:auto;max-width:1100px;padding:24px}section{background:#ffeaec;padding:20px;margin:18px 0;border:1px solid #6db1bf;border-radius:10px}table{border-collapse:collapse;width:100%;display:block;overflow:auto}td,th{padding:8px;border-bottom:1px solid #6db1bf;text-align:left}pre{white-space:pre-wrap;overflow-wrap:anywhere}svg{display:block;width:100%;max-height:650px;background:black}a{color:#154c76}li{margin:6px 0}@media print{details{display:block}section{break-inside:avoid}svg{max-height:400px}}</style><h1>OrganelleScope · analysis review</h1>',
        '<p>Generated '+text(datetime.now(timezone.utc).isoformat())+' · Version '+text(__version__)+'</p>',
        '<p>Read-only workspace snapshot. Source pixels are unchanged. Embedded images use the full stored intensity range, default channel colours, and no contrast enhancement. Measurements come from engine records; previews are for navigation.</p>',
        '<section id="source"><h2>'+text(info.filename)+'</h2><p>Source SHA-256: '+text(image['sha256'])+'</p>',details('Channels, axes and calibration',image['info']),details('Current analysis settings',{k:core.get(k) for k in ('thresholdMode','thresholds','target','measurementSource','processing')}),'</section>']
    results=(analysis or {}).get('results',[])
    parts.append('<nav><strong>Measured regions:</strong> '+(' · '.join('<a href="#roi-'+str(i)+'">ROI '+str(i+1)+' · Z '+str(row['roi']['z']+1)+'</a>' for i,row in enumerate(results)) or 'No matching ROI results. Calculate the current ROIs before exporting.')+'</nav>')
    planes={};embedded=set();limit=10
    for i,row in enumerate(results):
        roi=row['roi'];z=roi['z'];parts.append('<section id="roi-'+str(i)+'"><h2>ROI '+str(i+1)+' · '+text(roi['id'])+' · Z '+str(z+1)+'</h2>')
        if z not in planes and len(planes)<limit:
            composite=np.zeros((info.dimensions['Y'],info.dimensions['X'],3),dtype=np.float32)
            for c,color in enumerate([(1,0,0),(0,1,0),(0,0,1),(1,1,1)][:info.dimensions['C']]):
                plane=read_plane(folder/'source.tiff',info,c,z).astype(np.float32)/(2**info.bit_depth-1)
                composite+=plane[:,:,None]*color
            picture=Image.fromarray((np.clip(composite,0,1)*255).astype('uint8'));picture.thumbnail((1000,1000));buf=BytesIO();picture.save(buf,format='PNG')
            planes[z]='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
        if z in planes:
            w,h=info.dimensions['X'],info.dimensions['Y'];points=roi['points'];overlay=''
            if roi['kind']=='circle':
                cx,cy=points[0]['x'],points[0]['y'];radius=((points[1]['x']-cx)**2+(points[1]['y']-cy)**2)**.5
                diameter=roi.get('diameter_um');rx=diameter/(2*info.calibration['X'].value_um) if diameter else radius;ry=diameter/(2*info.calibration['Y'].value_um) if diameter else radius
                overlay=f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/>'
            else:overlay='<polygon points="'+' '.join(str(p['x'])+','+str(p['y']) for p in points)+'"/>'
            picture=(f'<image id="plane-{z}" width="{w}" height="{h}" href="{planes[z]}"/>' if z not in embedded else f'<use href="#plane-{z}"/>')
            embedded.add(z)
            parts.append(f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="ROI {i+1} on source Z plane {z+1}">{picture}<g fill="none" stroke="#ffff00" stroke-width="{max(w,h)/400}">{overlay}</g></svg>')
        else:parts.append('<p>Preview omitted: report embeds at most ten distinct Z planes. Geometry and measurements remain below.</p>')
        parts.append('<p>'+text(row.get('pixel_count'))+' pixels · '+text(row.get('area_um2'))+' µm²</p><table><tr><th>Channel A / B</th><th>Pearson</th><th>Spearman</th><th>Thresholded M1</th><th>Thresholded M2</th></tr>')
        for pair in row['pairs']:
            parts.append('<tr>'+''.join('<td>'+text(value)+'</td>' for value in [pair['label_a']+' / '+pair['label_b'],pair.get('pcc'),pair.get('spearman'),pair.get('thresholded_m1'),pair.get('thresholded_m2')])+'</tr>')
        parts.extend(['</table>',details('Complete engine values, thresholds, warnings and ROI geometry',row),'<a href="#source">Back to source and calibration</a></section>'])
    parts.extend(['<section><h2>3D, acquisition and sensitivity records</h2>','<p>Only reports matching this source and image metadata are included. Each record retains its own measurement settings; a saved report may use a different cuboid or recipe from the current controls.</p>',details('Matching reports',reading['reports']),details('Interpretation and exclusions',reading['notes']),'</section>',details('ROI calculation request and processing provenance',{k:(analysis or {}).get(k) for k in ('request','processing','algorithm_version','scope')}),'<p>M1 and M2 are directional intensity fractions; correlation and overlap do not establish molecular binding. Unavailable values are not zero. Review image regions, thresholds and experimental design before interpretation.</p><p><a href="https://github.com/mansonmyr/OrganelleScope/blob/main/MANUAL.md">Methods, metric definitions and references in the manual</a></p></html>'])
    return ''.join(parts)


def register_review_report(app,stored,authorized):
    @app.post('/api/images/{image_id}/review-report',dependencies=[Depends(authorized)],response_class=HTMLResponse)
    def report(image_id:str,options:WorkspaceContext):
        if options.image_id!=image_id:raise HTTPException(422,'Select the same image for this report.')
        if len(json.dumps(options.state))>8_000_000:raise HTTPException(422,'Workspace report exceeds the 8 MB record limit.')
        if not isinstance(options.state.get('core',{}),dict) or not isinstance(options.state.get('workspaces',{}),dict):raise HTTPException(422,'Invalid workspace report structure.')
        folder,image,_=stored(image_id)
        if options.expected_image_info!=image['info']:raise HTTPException(409,'Image settings changed; refresh before exporting.')
        digest=hashlib.sha256()
        with (folder/'source.tiff').open('rb') as stream:
            while chunk:=stream.read(1024*1024):digest.update(chunk)
        if digest.hexdigest()!=image['sha256']:raise HTTPException(409,'Source checksum changed; report export refused.')
        return build_review({'image':image,'state':options.state},folder)
