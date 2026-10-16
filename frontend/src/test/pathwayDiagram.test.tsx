import React from 'react';
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {EvidencePanel} from '../EvidencePanel';
import {json} from '../api';
vi.mock('../api',()=>({json:vi.fn()}));
beforeEach(()=>{
 Object.defineProperty(HTMLDialogElement.prototype,'showModal',{configurable:true,value(){this.setAttribute('open','');}});
 Object.defineProperty(HTMLDialogElement.prototype,'close',{configurable:true,value(){this.removeAttribute('open');this.dispatchEvent(new Event('close'));}});
});
afterEach(()=>{cleanup();vi.clearAllMocks();});
it('loads a KEGG diagram only when requested and supports zoom and close',async()=>{
 const base={database_version:'live KEGG',sources:[],limits:'bounded',citation_url:'https://www.kegg.jp',terms_url:'https://www.kegg.jp'};
 const image={pathway_id:'hsa04115',image_data_url:'data:image/png;base64,test',width:1000,height:700,source:{source_url:'https://rest.kegg.jp/get/hsa04115/image',retrieved_utc:'2026-10-16',cached:false,stale:false,response_sha256:'a'.repeat(64)},pathway_url:'https://www.kegg.jp/pathway/hsa04115',terms_url:'https://www.kegg.jp/kegg/rest/',interpretation:'Reference diagram; not experimental activity.'};
 vi.mocked(json).mockResolvedValueOnce({...base,rows:[{id:'hsa:7157',description:'TP53; tumor protein p53'}]}).mockResolvedValueOnce({...base,rows:[{gene:'hsa:7157',pathway_id:'hsa04115',name:'p53 signaling pathway'}]}).mockResolvedValueOnce(image);
 render(<EvidencePanel/>);fireEvent.change(screen.getByLabelText('Evidence database'),{target:{value:'kegg'}});
 fireEvent.click(screen.getByLabelText('Use these integrations for academic research.'));fireEvent.click(screen.getByText('Find identifier candidates'));
 await screen.findByText('Identifier candidates');fireEvent.click(screen.getByLabelText('hsa:7157 · TP53; tumor protein p53'));fireEvent.click(screen.getByText('Retrieve selected gene pathways'));
 await screen.findByRole('button',{name:'View hsa04115 pathway diagram'});expect(json).toHaveBeenCalledTimes(2);expect(screen.queryByRole('dialog')).toBeNull();
 fireEvent.click(screen.getByRole('button',{name:'View hsa04115 pathway diagram'}));await screen.findByRole('dialog');
 expect(JSON.parse(vi.mocked(json).mock.calls[2][1]!.body as string)).toEqual({pathway_id:'hsa04115',academic_use:true,offline_only:false});
 const diagram=screen.getByAltText('KEGG human pathway diagram hsa04115');expect(diagram.style.maxWidth).toBe('100%');
 fireEvent.change(screen.getByLabelText('Diagram zoom'),{target:{value:'150'}});expect(diagram.style.width).toBe('1500px');
 fireEvent.click(screen.getByText('Close diagram'));await waitFor(()=>expect(screen.queryByRole('dialog')).toBeNull());
});
