import React from 'react';
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import App from '../App';
import {json,request} from '../api';
vi.mock('../api',()=>({json:vi.fn(),request:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
it('keeps one preparation and validation workspace through saved-analysis restoration and recipe changes',async()=>{
 const calibration=Object.fromEntries(['X','Y','Z'].map(a=>[a,{value_um:.1,source:'OME',conflict:false,candidates:{}}]));
 const image={id:'test',sha256:'a'.repeat(64),options:{},info:{filename:'sample.tif',axes:'CZYX',source_axes:'CZYX',series_count:1,series_index:0,shape:[2,4,6,7],dtype:'uint16',bit_depth:16,decoded_bytes:672,dimensions:{X:7,Y:6,Z:4,C:2,T:1},channel_labels:['A','B'],calibration,warnings:[],needs_axis_confirmation:false}};
 vi.mocked(json).mockImplementation(async path=>(path==='/api/projects'||path==='/api/batch/sessions'||path==='/api/batch/runs')?[]:path==='/api/assistant/status'?{model:{name:'test',bytes:1},ready:false}:path==='/api/images'?[image]:{request:{rois:[],target_channel:0,threshold_mode:'zero',thresholds:[0,0],processing:{background:'none',offsets:[],radius_px:20,sigma_px:0}},scope:'native',results:[]});
 vi.mocked(request).mockResolvedValue({blob:async()=>new Blob()} as Response);URL.createObjectURL=vi.fn(()=>'blob:preview');URL.revokeObjectURL=vi.fn();
 render(<App/>);
 await screen.findByLabelText('Recent imports');fireEvent.change(screen.getByLabelText('Recent imports'),{target:{value:'test'}});
 await waitFor(()=>expect((screen.getByLabelText('Background method') as HTMLSelectElement).disabled).toBe(false));
 fireEvent.change(screen.getByLabelText('Background method'),{target:{value:'opening'}});fireEvent.click(screen.getByText('Apply recipe'));
 fireEvent.change(screen.getByLabelText('Measurement source'),{target:{value:'processed'}});
 await waitFor(()=>expect(screen.getAllByRole('heading',{name:'Background correction & smoothing'})).toHaveLength(1));
 fireEvent.click(screen.getByRole('button',{name:'Validation'}));
 expect(screen.getAllByRole('heading',{name:'Processing sensitivity & spatial controls'})).toHaveLength(1);
 expect(screen.queryByRole('heading',{name:'Background correction & smoothing'})).toBeNull();
 fireEvent.click(screen.getByRole('button',{name:'Molecular evidence'}));
 expect(screen.getByRole('heading',{name:'STRING associations & KEGG pathways'})).toBeTruthy();
});

it('keeps an independent batch draft when a different single-image project is opened',async()=>{
 const calibration=Object.fromEntries(['X','Y','Z'].map(a=>[a,{value_um:.1,source:'OME',conflict:false,candidates:{}}]));
 const info={filename:'queued.tif',axes:'CZYX',source_axes:'CZYX',series_count:1,series_index:0,shape:[2,4,6,7],dtype:'uint16',bit_depth:16,decoded_bytes:672,dimensions:{X:7,Y:6,Z:4,C:2,T:1},channel_labels:['A','B'],calibration,warnings:[],needs_axis_confirmation:false,acquisition:{}};
 const queued={id:'queued',sha256:'a'.repeat(64),options:{},info};const other={...queued,id:'other',info:{...info,filename:'other.tif'}};
 vi.mocked(json).mockImplementation(async(path,options)=>path==='/api/images'?(options?.method==='POST'?queued:[other]):path==='/api/projects'||path.startsWith('/api/batch/')?[]:path==='/api/assistant/status'?{model:{name:'test',bytes:1},ready:false}:Promise.reject(new Error('No saved analysis')));
 vi.mocked(request).mockResolvedValue({blob:async()=>new Blob()} as Response);URL.createObjectURL=vi.fn(()=>'blob:test');URL.revokeObjectURL=vi.fn();
 render(<App/>);fireEvent.click(screen.getByRole('button',{name:'Batch analysis'}));
 fireEvent.change(screen.getByLabelText('Upload batch TIFF images'),{target:{files:[new File(['x'],'queued.tif')]}});
 await screen.findByText('Imported 1 image(s). Draw and review ROIs for each image.');
 fireEvent.change(screen.getByLabelText('Recent imports'),{target:{value:'other'}});
 await waitFor(()=>expect(screen.getByText(/Image open. Saving a project is optional/)).toBeTruthy());
 fireEvent.click(screen.getByRole('button',{name:'Batch analysis'}));
 expect(screen.getByRole('heading',{name:'queued.tif'})).toBeTruthy();
});
