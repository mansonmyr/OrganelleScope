import React,{useState} from 'react';
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {SegmentationPanel} from '../SegmentationPanel';
import {ProcessingDiagnostics} from '../ProcessingDiagnostics';
import {ProjectStateProvider} from '../ProjectContext';
import {rawProcessing} from '../ProcessingPanel';
import {json,request} from '../api';
vi.mock('../api',()=>({json:vi.fn(),request:vi.fn()}));
const image:any={id:'image',info:{filename:'stack.tif',bit_depth:16,dimensions:{X:20,Y:20,Z:5,C:2},channel_labels:['A','B'],calibration:{X:{value_um:.1},Y:{value_um:.1},Z:{value_um:.5}}}};
afterEach(()=>{cleanup();vi.resetAllMocks();});
it('uses exactly the shared XYZ cuboid for segmentation and clears stale measurements when it moves',async()=>{
 vi.mocked(json).mockResolvedValue({object_count:1,foreground_voxels:8,threshold:10,objects:[],scope:'test',mesh:null});vi.mocked(request).mockResolvedValue({blob:async()=>new Blob()} as Response);URL.createObjectURL=vi.fn(()=>'blob:mask');URL.revokeObjectURL=vi.fn();
 function Host(){const [data,setData]=useState<Record<string,unknown>>({'OrthogonalWorkspace.bounds':{x0:3,x1:8,y0:4,y1:9,z0:1,z1:3}});return <ProjectStateProvider data={data} setData={setData}><button onClick={()=>setData(d=>({...d,'OrthogonalWorkspace.bounds':{x0:4,x1:9,y0:4,y1:9,z0:1,z1:3}}))}>Move test cuboid</button><SegmentationPanel image={image} processing={rawProcessing} rois={[]}/></ProjectStateProvider>;}
 render(<Host/>);fireEvent.click(screen.getByRole('button',{name:'Segment selected cuboid'}));await screen.findByText(/1 objects/);
 const call=vi.mocked(json).mock.calls.find(([p])=>p.endsWith('/segmentation'))!;expect(JSON.parse(call[1]!.body as string)).toMatchObject({x0:3,x1:8,y0:4,y1:9,z0:1,z1:3});
 fireEvent.click(screen.getByRole('button',{name:'Move test cuboid'}));await waitFor(()=>expect(screen.queryByText(/1 objects/)).toBeNull());
});
it('does not display processing diagnostics returned for a previous Z plane',async()=>{
 let resolve!:(v:any)=>void;vi.mocked(json).mockImplementation(()=>new Promise(r=>{resolve=r;}));
 const view=render(<ProcessingDiagnostics imageId="image" z={0} config={rawProcessing}/>);fireEvent.click(screen.getByRole('button',{name:'Measure processing changes'}));view.rerender(<ProcessingDiagnostics imageId="image" z={1} config={rawProcessing}/>);resolve({channels:[],scope:'STALE RESULT'});await waitFor(()=>expect(screen.queryByText('STALE RESULT')).toBeNull());expect((screen.getByRole('button',{name:'Measure processing changes'}) as HTMLButtonElement).disabled).toBe(false);
});
