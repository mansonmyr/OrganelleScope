import json
from urllib.parse import parse_qs,urlsplit
import pytest
from fastapi.testclient import TestClient
from organelle_scope.main import create_app
from organelle_scope.evidence import EvidenceClient,EvidenceRequest,query_urls


def test_identifier_queries_are_human_bounded_and_cannot_inject_urls():
    options=EvidenceRequest(provider='string',operation='map',identifiers=['TUBG1','PCNT'],academic_use=True)
    url=query_urls(options)[0];params=parse_qs(urlsplit(url).query)
    assert params['species']==['9606'] and params['identifiers']==['TUBG1\rPCNT']
    with pytest.raises(ValueError):query_urls(EvidenceRequest(provider='kegg',operation='map',identifiers=['https://bad.example']))
    with pytest.raises(ValueError):query_urls(EvidenceRequest(provider='kegg',operation='pathways',identifiers=['mmu:1']))
    with pytest.raises(ValueError):query_urls(EvidenceRequest(provider='string',operation='network',identifiers=['PCNT']))
    with pytest.raises(ValueError):EvidenceRequest(provider='string',operation='map',identifiers=['PCNT'],image='data')


def test_cache_offline_integrity_and_stale_label(tmp_path,monkeypatch):
    class Response:
        url='https://rest.kegg.jp/find/hsa/PCNT'
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):return b'hsa:5116\tPCNT; pericentrin\n'
    calls=[]
    monkeypatch.setattr('urllib.request.urlopen',lambda request,timeout,context:(calls.append(request.full_url) or Response()))
    client=EvidenceClient(tmp_path)
    first=client.fetch(Response.url);second=client.fetch(Response.url,True)
    assert not first['cached'] and second['cached'] and len(calls)==1
    assert first['response_sha256']==second['response_sha256']
    path=next(tmp_path.glob('*.json'));record=json.loads(path.read_text());record['retrieved_unix']=0;path.write_text(json.dumps(record))
    assert client.fetch(Response.url,True)['stale']
    with pytest.raises(ValueError,match='No saved'):client.fetch('https://rest.kegg.jp/find/hsa/TP53',True)


def test_evidence_routes_gate_academic_use_and_preserve_provenance(tmp_path,monkeypatch):
    calls=[]
    def fetch(self,url,offline=False):
        calls.append(url)
        if 'get_string_ids' in url:text=json.dumps([{'queryItem':'PCNT','preferredName':'PCNT','stringId':'9606.ENSP000001'}])
        elif '/network?' in url:text='[]'
        elif '/link/pathway/' in url:text='hsa:5116\tpath:hsa04110\n'
        elif '/list/' in url:text='hsa04110\tCell cycle - Homo sapiens\n'
        else:text='hsa:5116\tPCNT; pericentrin\n'
        return {'text':text,'source_url':url,'retrieved_utc':'2026-10-16T00:00:00+00:00','response_sha256':'a'*64,'cached':True,'stale':False}
    monkeypatch.setattr(EvidenceClient,'fetch',fetch)
    with TestClient(create_app(tmp_path,'token')) as client:
        h={'X-Session-Token':'token'};request={'provider':'string','operation':'map','identifiers':['PCNT']}
        assert client.post('/api/evidence/query',json=request).status_code==401
        assert client.post('/api/evidence/query',headers=h,json=request).status_code==422
        assert not calls
        report=client.post('/api/evidence/query',headers=h,json={**request,'academic_use':True}).json()
        assert report['rows'][0]['preferredName']=='PCNT' and report['database_version']=='12.5'
        assert 'text' not in report['sources'][0]
        pathway=client.post('/api/evidence/query',headers=h,json={'provider':'kegg','operation':'pathways','identifiers':['hsa:5116'],'academic_use':True}).json()
        assert pathway['rows'][0]['name']=='Cell cycle - Homo sapiens'
        assert len(pathway['sources'])==2


def test_missing_pathway_names_do_not_discard_valid_memberships(tmp_path,monkeypatch):
    def fetch(self,url,offline=False):
        if '/list/' in url:raise ValueError('provider unavailable')
        return {'text':'hsa:7157\tpath:hsa04115\n','source_url':url,'retrieved_utc':'2026-10-16T00:00:00+00:00','cached':True,'stale':False}
    monkeypatch.setattr(EvidenceClient,'fetch',fetch)
    with TestClient(create_app(tmp_path,'token')) as client:
        response=client.post('/api/evidence/query',headers={'X-Session-Token':'token'},json={'provider':'kegg','operation':'pathways','identifiers':['hsa:7157'],'academic_use':True})
        assert response.status_code==200
        result=response.json();assert result['rows'][0]['pathway_id']=='hsa04115'
        assert result['warnings'] and len(result['sources'])==1


def test_corrupt_cache_is_not_reused_offline(tmp_path):
    import hashlib
    url='https://rest.kegg.jp/find/hsa/PCNT'
    key=hashlib.sha256(url.encode()).hexdigest()
    (tmp_path/(key+'.json')).write_text(json.dumps({'source_url':url,'text':'altered','response_sha256':'bad','retrieved_unix':0}))
    with pytest.raises(ValueError,match='No saved'):EvidenceClient(tmp_path).fetch(url,True)


def test_exact_kegg_symbol_is_not_hidden_by_candidate_cap(tmp_path,monkeypatch):
    def fetch(self,url,offline=False):
        text=''.join(f'hsa:{1000+i}\tTP53BP{i}; other protein\n' for i in range(30))+'hsa:7157\tTP53, P53; tumor protein p53\n'
        return {'text':text,'source_url':url,'retrieved_utc':'2026-10-16T00:00:00+00:00','cached':False,'stale':False}
    monkeypatch.setattr(EvidenceClient,'fetch',fetch)
    with TestClient(create_app(tmp_path,'token')) as client:
        result=client.post('/api/evidence/query',headers={'X-Session-Token':'token'},json={'provider':'kegg','operation':'map','identifiers':['TP53'],'academic_use':True}).json()
        assert result['rows'][0]['id']=='hsa:7157'
        assert result['provider_row_count']==31 and result['truncated'] and len(result['rows'])==25


def test_pathway_png_is_validated_cached_and_academic_gated(tmp_path,monkeypatch):
    import io,base64
    from PIL import Image
    buf=io.BytesIO();Image.new('RGB',(120,80),'white').save(buf,format='PNG');payload=buf.getvalue()
    calls=[]
    class Response:
        url='https://rest.kegg.jp/get/hsa04115/image'
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):return payload
    monkeypatch.setattr('urllib.request.urlopen',lambda req,timeout,context:(calls.append(req.full_url) or Response()))
    with TestClient(create_app(tmp_path/'images','token')) as client:
        path='/api/evidence/kegg/pathway-image';h={'X-Session-Token':'token'};body={'pathway_id':'hsa04115','academic_use':True}
        assert client.post(path,json=body).status_code==401
        assert client.post(path,headers=h,json={**body,'academic_use':False}).status_code==422
        assert client.post(path,headers=h,json={**body,'pathway_id':'../../evil'}).status_code==422
        result=client.post(path,headers=h,json=body).json()
        assert (result['width'],result['height'])==(120,80)
        assert base64.b64decode(result['image_data_url'].split(',')[1])==payload
        assert not result['source']['cached'] and 'image_base64' not in result['source']
        cached=client.post(path,headers=h,json={**body,'offline_only':True}).json()
        assert cached['source']['cached'] and cached['image_data_url']==result['image_data_url']
        assert len(calls)==1
        assert client.post(path,headers=h,json={**body,'pathway_id':'hsa04010','offline_only':True}).status_code==422


def test_pathway_response_cannot_be_html(tmp_path,monkeypatch):
    class Response:
        url='https://rest.kegg.jp/get/hsa04115/image'
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):return b'<html>service unavailable</html>'
    monkeypatch.setattr('urllib.request.urlopen',lambda req,timeout,context:Response())
    with pytest.raises(ValueError,match='PNG'):EvidenceClient(tmp_path).fetch(Response.url,binary=True)
    assert list(tmp_path.glob('*.json'))==[]
