"""Small on-demand public identifier lookups. No images or measurements accepted."""
import hashlib
import base64
import io
from PIL import Image
import json
import re
import ssl
import certifi
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4
from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

STRING='https://version-12-5.string-db.org'
KEGG='https://rest.kegg.jp'


class EvidenceRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    provider: Literal['string','kegg']
    operation: Literal['map','network','pathways']
    identifiers: list[str] = Field(min_length=1,max_length=5)
    academic_use: bool = False
    offline_only: bool = False
    network_type: Literal['functional','physical'] = 'functional'
    required_score: int = Field(default=700,ge=0,le=1000)


def query_urls(options):
    if any(not re.fullmatch(r'[A-Za-z0-9_.:-]{1,64}',s) for s in options.identifiers):
        raise ValueError('Use protein identifiers without spaces or special characters (at most 64 characters each).')
    identifiers=options.identifiers
    if options.provider=='string':
        if options.operation=='map':
            return [STRING+'/api/json/get_string_ids?'+urllib.parse.urlencode({'identifiers':'\r'.join(identifiers),'species':9606,'limit':5,'echo_query':1,'caller_identity':'OrganelleScope'})]
        if options.operation=='network':
            if not all(re.fullmatch(r'9606\.ENSP[0-9]+',s) for s in identifiers):
                raise ValueError('Select resolved human STRING identifiers before retrieving a network.')
            return [STRING+'/api/json/network?'+urllib.parse.urlencode({'identifiers':'\r'.join(identifiers),'species':9606,'required_score':options.required_score,'network_type':options.network_type,'add_nodes':0,'caller_identity':'OrganelleScope'})]
    elif options.provider=='kegg':
        if options.operation=='map' and len(identifiers)==1:
            return [KEGG+('/list/'+identifiers[0] if re.fullmatch(r'hsa:[0-9]+',identifiers[0]) else '/find/hsa/'+urllib.parse.quote(identifiers[0],safe=''))]
        if options.operation=='pathways' and len(identifiers)==1 and re.fullmatch(r'hsa:[0-9]+',identifiers[0]):
            return [KEGG+'/link/pathway/'+identifiers[0]]
    raise ValueError('Unsupported lookup. KEGG accepts one human gene at a time.')


class PathwayImageRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    pathway_id: str = Field(pattern=r'^hsa[0-9]{5}$')
    academic_use: bool = False
    offline_only: bool = False


class EvidenceClient:
    def __init__(self,folder:Path):
        self.folder=folder;folder.mkdir(parents=True,exist_ok=True)
        self.lock=Lock();self.last_request=0.

    def fetch(self,url,offline=False,binary=False):
        key=hashlib.sha256(url.encode()).hexdigest();path=self.folder/(key+'.json')
        with self.lock:
            cached=None
            if path.exists():
                try:
                    cached=json.loads(path.read_text())
                    payload=base64.b64decode(cached['image_base64'],validate=True) if binary else cached['text'].encode()
                    if cached['source_url']!=url or not isinstance(cached['retrieved_unix'],(int,float)) or hashlib.sha256(payload).hexdigest()!=cached['response_sha256']:
                        cached=None
                except (ValueError,OSError,KeyError,TypeError):cached=None
            if cached and (offline or time.time()-cached['retrieved_unix']<7*86400):
                return {**cached,'cached':True,'stale':time.time()-cached['retrieved_unix']>=7*86400}
            if offline:raise ValueError('No saved evidence for this exact query. Switch off offline-only mode to fetch it.')
            time.sleep(max(0,1.05-(time.monotonic()-self.last_request)))
            self.last_request=time.monotonic()
            req=urllib.request.Request(url,headers={'User-Agent':'OrganelleScope-academic/0.1.6','Accept':'image/png' if binary else 'application/json,text/plain'})
            try:
                with urllib.request.urlopen(req,timeout=15,context=ssl.create_default_context(cafile=certifi.where())) as response:
                    if urllib.parse.urlsplit(response.url).hostname!=urllib.parse.urlsplit(url).hostname:
                        raise ValueError('The evidence provider redirected to a different host.')
                    limit=(4 if binary else 1)*1024*1024
                    raw=response.read(limit+1)
                    if len(raw)>limit:raise ValueError('Evidence response exceeds the bounded query size limit.')
                    if binary:
                        if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('KEGG did not return a PNG pathway diagram.')
                        with Image.open(io.BytesIO(raw)) as image:
                            width,height=image.size
                            if width*height>16_000_000:raise ValueError('The pathway diagram exceeds the 16 megapixel display limit.')
                            image.verify()
                    else:text=raw.decode('utf-8')
            except (urllib.error.URLError,TimeoutError,OSError,Image.DecompressionBombError) as exc:
                raise ValueError('Evidence service unavailable. Check the connection or use a previously cached query in offline-only mode.') from exc
            record={'source_url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'retrieved_unix':time.time(),
                    'response_sha256':hashlib.sha256(raw).hexdigest()}
            record.update({'image_base64':base64.b64encode(raw).decode('ascii'),'width':width,'height':height} if binary else {'text':text})
            temp=self.folder/(key+'.'+str(uuid4())+'.tmp');temp.write_text(json.dumps(record,ensure_ascii=False));temp.replace(path)
            # Bound actual cache storage, including JSON overhead; no bulk database download.
            files=sorted(self.folder.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
            size=0
            for index,old in enumerate(files):
                size+=old.stat().st_size
                if index>=64 or size>64*1024*1024:old.unlink()
            return {**record,'cached':False,'stale':False}


def register_evidence(app,data_dir,authorized):
    client=EvidenceClient(data_dir.parent/'evidence-cache')

    @app.post('/api/evidence/kegg/pathway-image',dependencies=[Depends(authorized)])
    def pathway_image(options:PathwayImageRequest):
        try:
            if not options.academic_use:raise ValueError('KEGG diagrams are enabled for academic research use only.')
            record=client.fetch(KEGG+'/get/'+options.pathway_id+'/image',options.offline_only,binary=True)
            return {'pathway_id':options.pathway_id,'image_data_url':'data:image/png;base64,'+record['image_base64'],
                    'width':record['width'],'height':record['height'],
                    'source':{k:v for k,v in record.items() if k!='image_base64'},
                    'pathway_url':'https://www.kegg.jp/pathway/'+options.pathway_id,
                    'terms_url':'https://www.kegg.jp/kegg/rest/',
                    'interpretation':'KEGG reference diagram for this human pathway. Displayed colours are KEGG annotations, not measured activity or a knockdown prediction.'}
        except (ValueError,KeyError,TypeError) as exc:raise HTTPException(422,str(exc)) from exc

    @app.post('/api/evidence/query',dependencies=[Depends(authorized)])
    def query(options:EvidenceRequest):
        try:
            if not options.academic_use:raise ValueError('These integrations are enabled for academic research use only.')
            urls=query_urls(options);records=[client.fetch(url,options.offline_only) for url in urls]
            record=records[0];warnings=[];total_rows=0
            if options.provider=='string':
                rows=json.loads(record['text'])
                if not isinstance(rows,list):raise ValueError('Unexpected STRING response.')
                # Mapping candidates remain explicit; the app never silently selects an ambiguous gene.
                total_rows=len(rows)
                rows=rows[:25] if options.operation=='map' else rows[:100]
            else:
                rows=[]
                for line in record['text'].splitlines():
                    if '\t' not in line:continue
                    a,b=line.split('\t',1)
                    rows.append({'id':a,'description':b} if options.operation=='map' else {'gene':a,'pathway_id':b.removeprefix('path:')})
                total_rows=len(rows)
                if options.operation=='map':
                    needle=options.identifiers[0].casefold()
                    rows.sort(key=lambda row:not (row['id'].casefold()==needle or needle in [alias.strip().casefold() for alias in row['description'].split(';',1)[0].split(',')]))
                rows=rows[:25]
                if options.operation=='pathways' and rows:
                    names_url=KEGG+'/list/pathway/hsa'
                    mapping={}
                    try:
                        names=client.fetch(names_url,options.offline_only);records.append(names)
                        mapping=dict(line.split('\t',1) for line in names['text'].splitlines() if '\t' in line)
                    except ValueError:
                        warnings.append('Pathway memberships were retrieved, but pathway names are unavailable. IDs and the membership source remain available.')
                    for i,r in enumerate(rows):r['name']=mapping.get('path:'+r['pathway_id'],mapping.get(r['pathway_id'],r['pathway_id'])) if i<10 else r['pathway_id']
            return {'provider':options.provider,'species':{'taxonomy_id':9606,'kegg':'hsa','name':'Homo sapiens'},
                    'query':options.model_dump(),'database_version':'12.5' if options.provider=='string' else 'live KEGG; see retrieval timestamp',
                    'rows':rows,'provider_row_count':total_rows,'truncated':total_rows>len(rows),'warnings':warnings,'sources':[{k:v for k,v in r.items() if k!='text'} for r in records],
                    'limits':'Up to 25 mapping/pathway results or 100 STRING edges; names for first 10 KEGG pathways. Not a complete database export.',
                    'citation_url':'https://string-db.org/help/' if options.provider=='string' else 'https://www.kegg.jp/kegg/kegg1.html',
                    'terms_url':'https://string-db.org/cgi/access?footer_active_subpage=licensing' if options.provider=='string' else 'https://www.kegg.jp/kegg/rest/',
                    'interpretation':'Database evidence is context, not measured binding, localization, causation or a knockdown prediction. Missing results do not establish absence of association.'}
        except (ValueError,KeyError,TypeError) as exc:raise HTTPException(422,str(exc)) from exc
