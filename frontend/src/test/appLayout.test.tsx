import React,{useState} from 'react';
import {afterEach,beforeEach,it,expect,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import App from '../App';
import {json,request} from '../api';
vi.mock('../api',()=>({json:vi.fn(),request:vi.fn()}));
vi.mock('../VolumeView',()=>({VolumeView:()=>{const [rotation,setRotation]=useState(0);return <button onClick={()=>setRotation(r=>r+1)}>Test volume rotation {rotation}</button>;}}));
vi.mock('../OrthogonalWorkspace',()=>({OrthogonalWorkspace:()=> <p>Test cuboid workspace</p>}));
vi.mock('../ValidationPanel',()=>({ValidationPanel:()=> <p>Test validation workspace</p>}));
vi.mock('../EvidencePanel',()=>({EvidencePanel:()=> <p>Test molecular workspace</p>}));
vi.mock('../AssistantPanel',()=>({AssistantPanel:()=> <p>Test assistant workspace</p>}));
vi.mock('../BatchPanel',()=>({BatchPanel:()=> <p>Test batch workspace</p>}));
const image={id:'test',info:{filename:'stack.tif',dimensions:{X:7,Y:6,Z:4,C:2,T:1},shape:[2,4,6,7],channel_labels:['A','B'],calibration:{X:{value_um:.1,candidates:{}},Y:{value_um:.2,candidates:{}},Z:{value_um:.5,candidates:{}}},warnings:[],axes:'CZYX',source_axes:'CZYX',series_index:0,series_count:1,decoded_bytes:672,bit_depth:16,dtype:'uint16',needs_axis_confirmation:false},options:{}};
beforeEach(()=>{
 vi.mocked(json).mockImplementation(async path=>{if(path==='/api/images')return [image];if(path==='/api/projects')return [];throw new Error('No saved analysis');});
 vi.mocked(request).mockResolvedValue({blob:async()=>new Blob()} as Response);
 URL.createObjectURL=vi.fn(()=>'blob:source');URL.revokeObjectURL=vi.fn();
});
afterEach(()=>{cleanup();vi.clearAllMocks();});
async function openImage(){render(<App/>);await screen.findByRole('option',{name:'stack.tif · test'});fireEvent.change(screen.getByRole('combobox',{name:'Recent imports'}),{target:{value:'test'}});await screen.findByRole('img',{name:'Composite Z plane 1'});}
it('places workspace navigation below a shared preview and retains its slice and drawing tool on tab changes',async()=>{
 await openImage();
 const viewer=screen.getByRole('region',{name:'Image preview'}),nav=screen.getByRole('navigation',{name:'Workspaces'});
 expect(viewer.compareDocumentPosition(nav)&Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
 fireEvent.change(screen.getByRole('slider',{name:'Z plane'}),{target:{value:'2'}});
 fireEvent.change(screen.getByRole('combobox',{name:'Drawing tool'}),{target:{value:'circle'}});
 const source=await screen.findByRole('img',{name:'Composite Z plane 3'});
 for(const tab of ['Validation','3D workspace','Molecular evidence','Batch analysis','Local assistant','Image & ROI']){
  fireEvent.click(screen.getByRole('button',{name:tab}));
  expect(screen.getByRole('region',{name:'Image preview'})).toBe(viewer);
  expect(screen.getByRole('img',{name:'Composite Z plane 3'})).toBe(source);
  expect((screen.getByRole('combobox',{name:'Drawing tool'}) as HTMLSelectElement).value).toBe('circle');
  expect(screen.getByRole('button',{name:'XY slice'}).getAttribute('aria-pressed')).toBe('true');
 }
});
it('keeps the 3D preview mounted and preserves its camera state when workspace tabs change',async()=>{
 await openImage();fireEvent.click(screen.getByRole('button',{name:'3D preview'}));
 fireEvent.click(screen.getByRole('button',{name:'Test volume rotation 0'}));
 const volume=screen.getByRole('button',{name:'Test volume rotation 1'});
 for(const tab of ['Validation','3D workspace','Molecular evidence','Image & ROI']){
  fireEvent.click(screen.getByRole('button',{name:tab}));
  expect(screen.getByRole('button',{name:'Test volume rotation 1'})).toBe(volume);
 }
 fireEvent.click(screen.getByRole('button',{name:'3D workspace'}));
 expect(screen.getByText('Test cuboid workspace')).toBeTruthy();
 expect(screen.getByRole('button',{name:'3D preview'}).getAttribute('aria-pressed')).toBe('true');
 await waitFor(()=>expect(screen.getByRole('button',{name:'Image & ROI'}).getAttribute('aria-pressed')).toBe('false'));
});
it.each([{core:{workspace:'images',mode:'volume'},tab:'3D workspace'},{core:{layout_version:2,workspace:'images',mode:'volume'},tab:'Image & ROI'}])('restores saved preview/workspace choices and migrates only legacy combined layouts: $tab',async({core,tab})=>{
 vi.mocked(json).mockImplementation(async path=>{
  if(path==='/api/images')return [image];
  if(path==='/api/projects')return [{id:'saved',name:'Saved layout',revision:1}];
  if(path==='/api/projects/saved')return {id:'saved',name:'Saved layout',revision:1,image,state:{core,workspaces:{}}};
  throw new Error('No saved analysis');
 });
 render(<App/>);await screen.findByRole('option',{name:'Saved layout · r1'});
 fireEvent.change(screen.getByRole('combobox',{name:'Open saved project'}),{target:{value:'saved'}});
 await screen.findByRole('button',{name:'Test volume rotation 0'});
 expect(screen.getByRole('button',{name:tab}).getAttribute('aria-pressed')).toBe('true');
});
