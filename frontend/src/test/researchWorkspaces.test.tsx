import React from 'react';
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {EvidencePanel} from '../EvidencePanel';
import {ValidationPanel} from '../ValidationPanel';
import {OrthogonalWorkspace} from '../OrthogonalWorkspace';
import {rawProcessing} from '../ProcessingPanel';
import {json,request,type ImageRecord} from '../api';
vi.mock('../api',()=>({json:vi.fn(),request:vi.fn()}));
const image={id:'image',info:{dimensions:{X:7,Y:6,Z:4,C:2},channel_labels:['A','B'],calibration:{X:{value_um:.1},Y:{value_um:.2},Z:{value_um:.5}}}} as unknown as ImageRecord;
const rois=[{id:'r',kind:'circle' as const,z:1,points:[{x:3,y:3},{x:5,y:3}]}];
beforeEach(()=>{vi.mocked(request).mockResolvedValue({blob:async()=>new Blob()} as Response);URL.createObjectURL=vi.fn(()=>'blob:sections');URL.revokeObjectURL=vi.fn();});
afterEach(()=>{cleanup();vi.clearAllMocks();});
describe('research workspaces',()=>{
 it('requires academic selection and explicit mapping before a STRING network query',async()=>{
  const mapping={rows:[{queryItem:'PCNT',preferredName:'PCNT',stringId:'9606.ENSP0001'}],database_version:'12.5',sources:[],limits:'bounded',citation_url:'https://string-db.org',terms_url:'https://string-db.org'};
  vi.mocked(json).mockResolvedValueOnce(mapping).mockResolvedValueOnce({...mapping,rows:[]});
  render(<EvidencePanel/>);
  expect((screen.getByText('Find identifier candidates') as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByLabelText('Use these integrations for academic research.'));
  fireEvent.click(screen.getByText('Find identifier candidates'));
  await screen.findByText('Identifier candidates');
  expect((screen.getByText('Retrieve selected network') as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByLabelText('PCNT → PCNT · 9606.ENSP0001'));
  fireEvent.click(screen.getByText('Retrieve selected network'));
  await waitFor(()=>expect(json).toHaveBeenCalledTimes(2));
  const body=JSON.parse(vi.mocked(json).mock.calls[1][1]!.body as string);
  expect(body.identifiers).toEqual(['9606.ENSP0001']);expect(body.operation).toBe('network');expect(body.academic_use).toBe(true);
 });
 it('runs matched sensitivity with zero thresholds instead of silently using automatic thresholds',async()=>{
  vi.mocked(json).mockResolvedValue({results:[]});
  render(<ValidationPanel image={image} rois={rois} processing={{...rawProcessing,background:'constant',offsets:[100,50]}} measurementProcessing={rawProcessing} thresholds={[0,0]} thresholdMode="costes" target={0}/>);
  expect((screen.getByText('Run spatial control') as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByText('Compare raw & processed ROIs'));
  await waitFor(()=>expect(json).toHaveBeenCalledTimes(1));
  const body=JSON.parse(vi.mocked(json).mock.calls[0][1]!.body as string);
  expect(body.threshold_mode).toBe('zero');expect(body.processing.offsets).toEqual([100,50]);
 });
 it('measures source cuboid coordinates and invalidates results when bounds change',async()=>{
  vi.mocked(json).mockResolvedValue({voxel_count:168,region_volume_um3:1.68,channels:[],pairs:[],scope:'source cuboid'});
  render(<OrthogonalWorkspace image={image} processing={rawProcessing}/>);
  fireEvent.click(screen.getByText('Measure 3D cuboid'));
  await screen.findByText('Export 3D report');
  const body=JSON.parse(vi.mocked(json).mock.calls[0][1]!.body as string);
  expect(body).toMatchObject({x0:0,x1:6,y0:0,y1:5,z0:0,z1:3,processing:rawProcessing});
  fireEvent.change(screen.getByLabelText('X start'),{target:{value:'2'}});
  expect(screen.queryByText('Export 3D report')).toBeNull();
  await waitFor(()=>expect(request).toHaveBeenCalledTimes(3));
  expect(vi.mocked(request).mock.calls.map(c=>c[0])).toEqual(expect.arrayContaining([expect.stringContaining('axis=XY'),expect.stringContaining('axis=XZ'),expect.stringContaining('axis=YZ')]));
 });
});

it('moves the cuboid from a section click and arrow key, then measures those exact bounds',async()=>{
 const larger={...image,info:{...image.info,dimensions:{X:100,Y:100,Z:8,C:2}}};
 vi.mocked(json).mockResolvedValue({voxel_count:32768,region_volume_um3:10,channels:[],pairs:[],scope:'source cuboid'});
 render(<OrthogonalWorkspace image={larger} processing={rawProcessing}/>);
 const section=screen.getByRole('img',{name:'XY linked source section'});
 Object.defineProperty(section,'getBoundingClientRect',{value:()=>({left:0,top:0,width:100,height:100})});
 Object.defineProperty(section,'setPointerCapture',{value:()=>{}});Object.defineProperty(section,'hasPointerCapture',{value:()=>false});
 const Pointer=window.PointerEvent;window.PointerEvent=MouseEvent as typeof PointerEvent;
 try{
  fireEvent.pointerDown(section,{clientX:50,clientY:50,button:0});fireEvent.pointerMove(section,{clientX:60,clientY:55,button:0});fireEvent.pointerUp(section,{clientX:60,clientY:55,button:0});
  expect((screen.getByLabelText('X start') as HTMLInputElement).value).toBe('28');
  expect((screen.getByLabelText('Y start') as HTMLInputElement).value).toBe('23');
  fireEvent.pointerDown(section,{clientX:95,clientY:95,button:0});fireEvent.pointerUp(section,{clientX:95,clientY:95,button:0});
 }finally{window.PointerEvent=Pointer;}
 expect((screen.getByLabelText('X start') as HTMLInputElement).value).toBe('36');
 expect((screen.getByLabelText('Y start') as HTMLInputElement).value).toBe('36');
 fireEvent.keyDown(section,{key:'ArrowLeft',shiftKey:true});
 expect((screen.getByLabelText('X start') as HTMLInputElement).value).toBe('26');
 fireEvent.click(screen.getByText('Measure 3D cuboid'));await screen.findByText('Export 3D report');
 const call=vi.mocked(json).mock.calls.find(c=>c[0].endsWith('/cuboid'))!;
 expect(JSON.parse(call[1]!.body as string)).toMatchObject({x0:26,x1:89,y0:36,y1:99,z0:0,z1:7});
 fireEvent.keyDown(section,{key:'ArrowLeft'});expect(screen.queryByText('Export 3D report')).toBeNull();
});
it('resizes the cuboid in XY and Z, clears old results and measures the new inclusive bounds',async()=>{
 vi.mocked(json).mockResolvedValue({voxel_count:168,region_volume_um3:1.68,channels:[],pairs:[],scope:'source cuboid'});
 render(<OrthogonalWorkspace image={image} processing={rawProcessing}/>);
 fireEvent.click(screen.getByText('Measure 3D cuboid'));await screen.findByText('Export 3D report');
 fireEvent.change(screen.getByLabelText('Width X (voxels)'),{target:{value:'3'}});
 fireEvent.change(screen.getByLabelText('Height Y (voxels)'),{target:{value:'2'}});
 fireEvent.change(screen.getByLabelText('Depth Z (slices)'),{target:{value:'2'}});
 expect(screen.queryByText('Export 3D report')).toBeNull();
 fireEvent.click(screen.getByText('Measure 3D cuboid'));await screen.findByText('Export 3D report');
 expect(JSON.parse(vi.mocked(json).mock.calls[vi.mocked(json).mock.calls.length-1][1]!.body as string)).toMatchObject({x0:2,x1:4,y0:2,y1:3,z0:1,z1:2});
 expect(screen.getAllByText('0.300 µm extent')).toHaveLength(1);
 fireEvent.change(screen.getByLabelText('Depth Z (slices)'),{target:{value:'4'}});
 expect((screen.getByLabelText('Z start') as HTMLInputElement).value).toBe('0');
 expect((screen.getByLabelText('Z end') as HTMLInputElement).value).toBe('3');
});
