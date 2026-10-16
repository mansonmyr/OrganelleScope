import React,{StrictMode,useState} from 'react';
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {ProjectStateProvider,useProjectState,type WorkspaceData} from '../ProjectContext';
import {ValidationPanel} from '../ValidationPanel';
import {OrthogonalWorkspace} from '../OrthogonalWorkspace';
import {AssistantPanel} from '../AssistantPanel';
import {rawProcessing} from '../ProcessingPanel';
import {json,request,type ImageRecord} from '../api';
vi.mock('../api',()=>({json:vi.fn(),request:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
const image={id:'test',info:{dimensions:{X:7,Y:6,Z:4,C:2},channel_labels:['A','B'],calibration:{X:{value_um:.1},Y:{value_um:.2},Z:{value_um:.5}}}} as unknown as ImageRecord;
const rois=[{id:'r',kind:'circle' as const,z:1,points:[{x:3,y:3},{x:5,y:3}]}];
const thresholds=[0,0];
function Saved({children}:{children:React.ReactNode}){
 const [data,setData]=useState<WorkspaceData>({'ValidationPanel.reference':{passed:true,checks:[1],fiji_benchmark_status:'pending'},'ValidationPanel.spatial':{observed_pearson:.7,tail_probability:.01,null_quantiles:[.1,.2,.3],iterations:199,interpretation:'restored spatial result'},'OrthogonalWorkspace.report':{voxel_count:168,region_volume_um3:1.68,channels:[],pairs:[],scope:'restored cuboid'},'OrthogonalWorkspace.bounds':{x0:0,x1:6,y0:0,y1:5,z0:0,z1:3}});
 return <ProjectStateProvider data={data} setData={setData}>{children}</ProjectStateProvider>;
}
it('retains restored 3D reports through StrictMode and invalidates only after a bounds edit',async()=>{
 vi.mocked(request).mockResolvedValue({blob:async()=>new Blob()} as Response);URL.createObjectURL=vi.fn(()=>'blob:test');URL.revokeObjectURL=vi.fn();
 render(<StrictMode><Saved><OrthogonalWorkspace image={image} processing={rawProcessing}/></Saved></StrictMode>);
 expect(screen.getByText('Export 3D report')).toBeTruthy();
 fireEvent.change(screen.getByLabelText('X start'),{target:{value:'1'}});
 await waitFor(()=>expect(screen.queryByText('Export 3D report')).toBeNull());
});
it('retains restored validation reports across mount and clears affected reports after settings change',()=>{
 const props={image,rois,processing:rawProcessing,measurementProcessing:rawProcessing,thresholds,thresholdMode:'zero',target:0};
 const view=render(<StrictMode><Saved><ValidationPanel {...props}/></Saved></StrictMode>);
 expect(screen.getByText(/Numeric references: all passed/)).toBeTruthy();
 expect(screen.getByText(/Observed Pearson/)).toBeTruthy();
 view.rerender(<StrictMode><Saved><ValidationPanel {...props} thresholds={[20,20]}/></Saved></StrictMode>);
 expect(screen.queryByText(/Observed Pearson/)).toBeNull();
 expect(screen.getByText(/Numeric references: all passed/)).toBeTruthy();
});
it('sends local assistant requests with online permission off and retains the answer and tool record',async()=>{
 vi.mocked(json).mockImplementation(async path=>path==='/api/assistant/status'?{model:{name:'Local test',bytes:2707513696},ready:true,running:true,model_available:true,runtime_available:true}:{answer:'Controls remain necessary. [project]',status:'AI draft',project_revision:2,elapsed_seconds:1,sources:[{id:'project',title:'Saved project'}],audit:[{tool:'inspect_project',result:{revision:2}}]});
 render(<Saved><AssistantPanel projectId="saved-project"/></Saved>);
 await screen.findByText(/Local test/);
 fireEvent.change(screen.getByLabelText('Ask the local assistant'),{target:{value:'What controls are missing?'}});
 fireEvent.click(screen.getByText('Ask local assistant'));
 await screen.findByText('Controls remain necessary. [project]');
 const call=vi.mocked(json).mock.calls.find(c=>c[0]==='/api/assistant/chat')!;
 expect(JSON.parse(call[1]!.body as string)).toMatchObject({project_id:'saved-project',allow_online:false,history:[]});
 expect(screen.getByText('Application tool record · 1 calls')).toBeTruthy();
});

it('ignores late workspace updates from a project that has been closed',async()=>{
 let late:((value:string)=>void)|undefined;
 function Child(){const [value,setValue]=useProjectState('late','');late=setValue;return <span>{value||'empty'}</span>;}
 function Host({generation}:{generation:number}){const [data,setData]=useState<WorkspaceData>({});return <><ProjectStateProvider key={generation} data={data} setData={setData}><Child/></ProjectStateProvider><output>{JSON.stringify(data)}</output></>;}
 const view=render(<Host generation={1}/>);const old=late!;
 view.rerender(<Host generation={2}/>);old('stale response');
 expect(screen.getByText('empty')).toBeTruthy();expect(screen.getByText('{}')).toBeTruthy();
});
