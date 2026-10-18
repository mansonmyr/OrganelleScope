import React from 'react';
import {afterEach,beforeEach,it,expect,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {BatchPanel} from '../BatchPanel';
import {json,request,type ImageRecord} from '../api';
vi.mock('../api',()=>({json:vi.fn(),request:vi.fn()}));
const image=(id:string)=>({id,sha256:'a'.repeat(64),options:{},info:{filename:id+'.tif',axes:'CZYX',series_index:0,series_count:1,dimensions:{X:100,Y:100,Z:3,C:2},channel_labels:['A','B'],bit_depth:16,needs_axis_confirmation:false,warnings:[],calibration:{X:{value_um:.1,conflict:false},Y:{value_um:.2,conflict:false},Z:{value_um:.3,conflict:false}}}} as unknown as ImageRecord);
beforeEach(()=>{
 URL.createObjectURL=vi.fn(()=>'blob:preview');URL.revokeObjectURL=vi.fn();vi.stubGlobal('PointerEvent',MouseEvent);
 Object.defineProperty(SVGSVGElement.prototype,'createSVGPoint',{configurable:true,value(){return {x:0,y:0,matrixTransform(){return {x:this.x,y:this.y};}};}});
 Object.defineProperty(SVGSVGElement.prototype,'getScreenCTM',{configurable:true,value:()=>({inverse:()=>({})})});
 vi.mocked(request).mockResolvedValue({blob:async()=>new Blob()} as Response);
});
afterEach(()=>{cleanup();vi.clearAllMocks();vi.unstubAllGlobals();});
it('keeps per-image manual ROIs, gates analysis on review and clears review after size changes',async()=>{
 let n=0;let saved:any;
 vi.mocked(json).mockImplementation(async(path,options)=>{
  if(path==='/api/images')return image('image'+(++n));
  if(path==='/api/batch/sessions'&&options?.method==='POST'){saved=JSON.parse(options.body as string);return {...saved,id:'batch',revision:1};}
  if(path==='/api/batch/runs'&&options?.method==='POST')return {id:'run',name:'test',status:'completed',items:[]};
  return [];
 });
 render(<BatchPanel/>);await waitFor(()=>expect(json).toHaveBeenCalledWith('/api/batch/runs'));
 fireEvent.change(screen.getByLabelText('Upload batch TIFF images'),{target:{files:[new File(['a'],'a.tif'),new File(['b'],'b.tif')]}});
 await screen.findByText('Imported 2 image(s). Draw and review ROIs for each image.');
 const run=screen.getByText('Analyze reviewed batch') as HTMLButtonElement;expect(run.disabled).toBe(true);
 function draw(x:number,y:number){fireEvent.pointerDown(screen.getByLabelText('ROI drawing surface'),{clientX:x,clientY:y,button:0});}
 draw(40,40);fireEvent.click(screen.getByLabelText('Reviewed image ROIs and settings'));expect(run.disabled).toBe(true);
 fireEvent.change(screen.getByLabelText('Batch image queue'),{target:{value:'1'}});expect(screen.queryByText('Delete ROI 1')).toBeNull();
 draw(60,60);fireEvent.click(screen.getByLabelText('Reviewed image ROIs and settings'));expect(run.disabled).toBe(false);
 const size=screen.getByLabelText(/Diameter in micrometers for/);fireEvent.change(size,{target:{value:'3'}});fireEvent.click(screen.getByText('Apply diameter'));
 expect((screen.getByLabelText('Reviewed image ROIs and settings') as HTMLInputElement).checked).toBe(false);expect(run.disabled).toBe(true);
 fireEvent.click(screen.getByLabelText('Reviewed image ROIs and settings'));fireEvent.click(run);
 await screen.findByText('test · completed');expect(saved.items).toHaveLength(2);
 expect(saved.items[0].analysis.rois[0]).toMatchObject({diameter_um:2,points:[{x:40,y:40},{x:50,y:40}]});
 expect(saved.items[1].analysis.rois[0]).toMatchObject({diameter_um:3,points:[{x:60,y:60},{x:75,y:60}]});
 expect(saved.items.every((i:any)=>i.reviewed)).toBe(true);
});
it('allows correcting batch channel identity and requires review again while retaining ROIs',async()=>{
 const original=image('one');let saved:any;
 vi.mocked(json).mockImplementation(async(path,options)=>{
  if(path==='/api/images')return original;
  if(path==='/api/images/one/channels')return {...original,info:{...original.info,channel_labels:['Alpha-tubulin','GM130']}};
  if(path==='/api/batch/sessions'&&options?.method==='POST'){saved=JSON.parse(options.body as string);return {...saved,id:'batch',revision:1};}
  return [];
 });
 render(<BatchPanel/>);
 fireEvent.change(screen.getByLabelText('Upload batch TIFF images'),{target:{files:[new File(['a'],'a.tif')]}});
 await screen.findByText('Imported 1 image(s). Draw and review ROIs for each image.');
 fireEvent.pointerDown(screen.getByLabelText('ROI drawing surface'),{clientX:40,clientY:40,button:0});
 fireEvent.click(screen.getByLabelText('Reviewed image ROIs and settings'));
 expect((screen.getByText('Analyze reviewed batch') as HTMLButtonElement).disabled).toBe(false);
 fireEvent.change(screen.getByLabelText('Channel 1 name'),{target:{value:'Alpha-tubulin'}});
 fireEvent.change(screen.getByLabelText('Channel 2 name'),{target:{value:'GM130'}});
 fireEvent.click(screen.getByText('Apply channel names'));
 await waitFor(()=>expect((screen.getByLabelText('Reviewed image ROIs and settings') as HTMLInputElement).checked).toBe(false));
 expect(screen.getByText('Delete ROI 1')).toBeTruthy();
 expect((screen.getByText('Analyze reviewed batch') as HTMLButtonElement).disabled).toBe(true);
 fireEvent.click(screen.getByText('Save batch'));await waitFor(()=>expect(saved).toBeTruthy());
 expect(saved.items[0].image.info.channel_labels).toEqual(['Alpha-tubulin','GM130']);
 expect(saved.items[0].analysis.rois).toHaveLength(1);
});
