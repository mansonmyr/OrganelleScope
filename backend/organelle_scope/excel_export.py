"""Portable, formula-free OOXML export of authoritative engine values."""
from io import BytesIO
import json
import math
import re
from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZipFile, ZIP_DEFLATED

NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
INVALID=re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f]')


def column(n):
    result=''
    while n:
        n,r=divmod(n-1,26);result=chr(65+r)+result
    return result


def xml(element): return tostring(element,encoding='utf-8',xml_declaration=True)


def workbook(sheets):
    """Only literal strings and finite numeric cells. Never interpret user input."""
    if sum(len(row) for _,rows in sheets for row in rows)>2_000_000:
        raise ValueError('Excel export exceeds the two-million-cell limit. Export full JSON or use smaller batches.')
    output=BytesIO()
    with ZipFile(output,'w',ZIP_DEFLATED) as z:
        types=Element('Types',xmlns='http://schemas.openxmlformats.org/package/2006/content-types')
        for ext,typ in [('rels','application/vnd.openxmlformats-package.relationships+xml'),('xml','application/xml')]:SubElement(types,'Default',Extension=ext,ContentType=typ)
        for name,typ in [('workbook','sheet.main'),('styles','styles')]:
            SubElement(types,'Override',PartName=f'/xl/{name}.xml',ContentType=f'application/vnd.openxmlformats-officedocument.spreadsheetml.{typ}+xml')
        book=Element('workbook',xmlns=NS);sheetlist=SubElement(book,'sheets')
        rels=Element('Relationships',xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
        for index,(name,rows) in enumerate(sheets,1):
            if len(rows)>1_048_576:raise ValueError('Too many worksheet rows. Export full JSON or split the batch.')
            SubElement(sheetlist,'sheet',name=name,sheetId=str(index),attrib={f'{{{REL}}}id':f'rId{index}'})
            SubElement(rels,'Relationship',Id=f'rId{index}',Type=REL+'/worksheet',Target=f'worksheets/sheet{index}.xml')
            SubElement(types,'Override',PartName=f'/xl/worksheets/sheet{index}.xml',ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml')
            sheet=Element('worksheet',xmlns=NS)
            views=SubElement(sheet,'sheetViews');view=SubElement(views,'sheetView',workbookViewId='0')
            SubElement(view,'pane',ySplit='1',topLeftCell='A2',activePane='bottomLeft',state='frozen')
            cols=SubElement(sheet,'cols')
            widths=[]
            for c in range(max(map(len,rows),default=1)):
                longest=max((len(str(row[c])) for row in rows if c<len(row) and row[c] is not None),default=0)
                width=110 if name=='Read me' and c==1 else min(70,max(24,longest+2))
                widths.append(width)
                SubElement(cols,'col',min=str(c+1),max=str(c+1),width=str(width),customWidth='1')
            data=SubElement(sheet,'sheetData')
            for ri,row in enumerate(rows,1):
                lines=max((sum(max(1,math.ceil(len(part)/max(1,widths[ci]-2))) for part in str(value).split('\n')) for ci,value in enumerate(row) if value is not None),default=1)
                node=SubElement(data,'row',r=str(ri),ht=str(min(409,18*lines+4)),customHeight='1')
                for ci,value in enumerate(row,1):
                    if value is None:continue
                    cell=SubElement(node,'c',r=f'{column(ci)}{ri}',s='1' if ri==1 else '0')
                    if isinstance(value,(int,float)) and not isinstance(value,bool):
                        if not math.isfinite(value):raise ValueError('Non-finite result cannot be exported.')
                        SubElement(cell,'v').text=str(value)
                    else:
                        text=INVALID.sub('',str(value))
                        if len(text)>32767:raise ValueError('A worksheet cell exceeds the Excel text limit; export JSON instead.')
                        cell.set('t','inlineStr');inline=SubElement(cell,'is');SubElement(inline,'t',attrib={'{http://www.w3.org/XML/1998/namespace}space':'preserve'}).text=text
            if len(rows)>1 and rows[0]:SubElement(sheet,'autoFilter',ref=f'A1:{column(len(rows[0]))}{len(rows)}')
            z.writestr(f'xl/worksheets/sheet{index}.xml',xml(sheet))
        SubElement(rels,'Relationship',Id='styles',Type=REL+'/styles',Target='styles.xml')
        z.writestr('xl/workbook.xml',xml(book));z.writestr('xl/_rels/workbook.xml.rels',xml(rels));z.writestr('[Content_Types].xml',xml(types))
        root=Element('Relationships',xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
        SubElement(root,'Relationship',Id='rId1',Type=REL+'/officeDocument',Target='xl/workbook.xml');z.writestr('_rels/.rels',xml(root))
        z.writestr('xl/styles.xml',f'''<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="{NS}"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FFFFECD1"/><name val="Calibri"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF15616D"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"><alignment vertical="top" wrapText="1"/></xf><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"><alignment vertical="top" wrapText="1"/></xf></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>''')
    return output.getvalue()


def export_batch(run):
    if sum(len(r['points'])*8 for i in run['items'] for r in i['analysis']['rois'])>1_800_000:
        raise ValueError('ROI geometry exceeds the Excel export budget. Export full JSON or split the batch.')
    notes=[['Item','Meaning'],['Batch',run['name']],['Run ID',run['id']],['Application version',run['app_version']],['Status',run['status']],['Started UTC',run['started']],['Finished UTC',run.get('finished')],
           ['Units','XY coordinates are pixel-center coordinates; Z planes and channel numbers are one-based here. Diameter and calibration are in micrometers.'],
           ['Missing values','Blank numeric cells mean unavailable or undefined, never zero. Inspect warnings and threshold status.'],
           ['Interpretation','Separate XY-plane ROI measurements. No pooled p-values, biological replicate inference, binding probability or super-resolution claim. Gaussian LRT is a descriptive covariance statistic.'],
           ['Review','Every image requires manual ROI and settings review before starting. Processing does not change source TIFF pixels.'],
           ['Reproducibility','Export full JSON alongside this workbook for complete engine results, image metadata and provenance. See MANUAL.md#part-vi--roi-measurements-and-channel-associations and MANUAL.md#part-ix--batch-analysis-and-excel.'],
           ['Validation','Engineering tested; independent microscopy benchmarks and biological validation remain pending.']]
    summary=[['Image ID','Filename','Source SHA-256','Status','Error','Experiment','Cell','Condition','ROI count','Reviewed']]
    settings=[['Image ID','Axes','Series index (zero based)','X µm/pixel','Y µm/pixel','Z µm/plane','Calibration details JSON','Channel labels JSON','Threshold mode','Manual thresholds JSON','Target channel (one based)','Processing JSON','Algorithm version']]
    geometry=[['Image ID','ROI ID','Kind','Z plane','Diameter µm','Vertex (one based)','X pixel','Y pixel']]
    pairs=[['Image ID','ROI ID','Z plane','Channel A','Channel B','Pixels','Area µm²','Pearson r','Spearman rho','MOC','M1 (>0)','M2 (>0)','Thresholded M1','Thresholded M2','Threshold A','Threshold B','Threshold status','Gaussian LRT (descriptive)','Warnings']]
    channels=[['Image ID','ROI ID','Channel','Mean','SD','Sum']]
    regression=[['Image ID','ROI ID','R squared','Coefficient ratio','Betas JSON','Warnings']]
    for item in run['items']:
        ident=item['image_id'];image=item['image'];info=image['info'];a=item['analysis'];result=item.get('result',{})
        summary.append([ident,info['filename'],image['sha256'],item['status'],item.get('error'),item['experiment'],item['cell'],item['condition'],len(a['rois']),str(item['reviewed'])])
        settings.append([ident,info['axes'],info['series_index'],*[info['calibration'][d]['value_um'] for d in 'XYZ'],json.dumps(info['calibration']),json.dumps(info['channel_labels']),a['threshold_mode'],json.dumps(a['thresholds']),a['target_channel']+1,json.dumps(a['processing']),result.get('algorithm_version')])
        for roi in a['rois']:
            for j,point in enumerate(roi['points'],1):geometry.append([ident,roi['id'],roi['kind'],roi['z']+1,roi.get('diameter_um'),j,point['x'],point['y']])
        for roi in result.get('results',[]):
            rid=roi['roi']['id']
            for p in roi['pairs']:
                pairs.append([ident,rid,roi['roi']['z']+1,p['label_a'],p['label_b'],roi['pixel_count'],roi['area_um2'],*[p[k] for k in ('pcc','spearman','moc','m1','m2','thresholded_m1','thresholded_m2')],p['thresholds']['a'],p['thresholds']['b'],p['thresholds']['status'],p['gaussian_lrt_statistic'],'; '.join(roi['warnings']+p['warnings']+[p['gaussian_lrt_note']])])
            for c in roi['channel_summary']:channels.append([ident,rid,c['label'],c['mean'],c['std'],c['sum']])
            reg=roi['regression'];regression.append([ident,rid,reg['r_squared'],reg['coefficient_ratio'],json.dumps(reg['betas']),'; '.join(reg['warnings'])])
    return workbook([('Read me',notes),('Images',summary),('Settings',settings),('ROI geometry',geometry),('Colocalization',pairs),('Intensities',channels),('Regression',regression)])
