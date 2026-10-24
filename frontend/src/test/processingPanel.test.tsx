import React from 'react';
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {ProcessingPanel,rawProcessing} from '../ProcessingPanel';
import {request} from '../api';
vi.mock('../api',()=>({request:vi.fn()}));
beforeEach(()=>{vi.mocked(request).mockResolvedValue({blob:async()=>new Blob()} as Response);URL.createObjectURL=vi.fn(()=>'blob:comparison');URL.revokeObjectURL=vi.fn();});
afterEach(()=>{cleanup();vi.clearAllMocks();});
describe('processing recipe workflow',()=>{
 it('applies per-channel offsets only after an explicit action and resets to raw',async()=>{
  const onChange=vi.fn();render(<ProcessingPanel imageId="test" z={2} labels={['A','B']} bitDepth={16} value={rawProcessing} disabled={false} onChange={onChange}/>);
  fireEvent.change(screen.getByLabelText('Background method'),{target:{value:'constant'}});
  fireEvent.change(screen.getByLabelText('A offset'),{target:{value:'100.5'}});
  fireEvent.change(screen.getByLabelText('B offset'),{target:{value:'50'}});
  expect(onChange).not.toHaveBeenCalled();fireEvent.click(screen.getByText('Apply recipe'));
  expect(onChange).toHaveBeenLastCalledWith({...rawProcessing,background:'constant',offsets:[100.5,50]});
  await waitFor(()=>expect(request).toHaveBeenCalled());
  expect(JSON.parse(vi.mocked(request).mock.calls[0][1]!.body as string)).toEqual(rawProcessing);
  fireEvent.click(screen.getByText('Reset to raw'));expect(onChange).toHaveBeenLastCalledWith(rawProcessing);
 });
 it('prevents invalid radius settings and disables mutation while measurements are running',()=>{
  const props={imageId:'test',z:0,labels:['A'],bitDepth:16,value:rawProcessing,onChange:vi.fn()};
  const {rerender}=render(<ProcessingPanel {...props} disabled={false}/>);
  fireEvent.change(screen.getByLabelText('Background method'),{target:{value:'opening'}});
  fireEvent.change(screen.getByLabelText('Background radius (XY pixels)'),{target:{value:'2.5'}});
  expect((screen.getByText('Apply recipe') as HTMLButtonElement).disabled).toBe(true);
  rerender(<ProcessingPanel {...props} disabled/>);
  expect((screen.getByLabelText('Background method') as HTMLSelectElement).disabled).toBe(true);
  expect((screen.getByText('Reset to raw') as HTMLButtonElement).disabled).toBe(true);
 });
});
it('exposes rolling-ball radius and native intensity height and validates the CPU limit',()=>{
 const onChange=vi.fn();render(<ProcessingPanel imageId="test" z={0} labels={['A']} bitDepth={16} value={rawProcessing} disabled={false} onChange={onChange}/>);
 fireEvent.change(screen.getByLabelText('Background method'),{target:{value:'rolling_ball'}});
 fireEvent.change(screen.getByLabelText('Kernel height (native intensity units)'),{target:{value:'1500'}});
 fireEvent.change(screen.getByLabelText('Background radius (XY pixels)'),{target:{value:'30'}});
 fireEvent.click(screen.getByText('Apply recipe'));
 expect(onChange).toHaveBeenLastCalledWith({...rawProcessing,background:'rolling_ball',offsets:[0],radius_px:30,rolling_height:1500});
 fireEvent.change(screen.getByLabelText('Background radius (XY pixels)'),{target:{value:'101'}});
 expect((screen.getByText('Apply recipe') as HTMLButtonElement).disabled).toBe(true);
});
it('keeps cleared radius, ball height and smoothing fields blank until valid numbers are entered',async()=>{
 const onChange=vi.fn();render(<ProcessingPanel imageId="test" z={0} labels={['A']} bitDepth={16} value={rawProcessing} disabled={false} onChange={onChange}/>);
 fireEvent.change(screen.getByLabelText('Background method'),{target:{value:'rolling_ball'}});
 const fields=['Background radius (XY pixels)','Kernel height (native intensity units)','Gaussian smoothing σ (XY pixels)'].map(name=>screen.getByLabelText(name) as HTMLInputElement);
 for(const field of fields){fireEvent.change(field,{target:{value:''}});fireEvent.blur(field);expect(field.value).toBe('');}
 fireEvent.click(screen.getByText('Apply recipe'));expect(onChange).not.toHaveBeenCalled();
 expect((screen.getByText('Apply recipe') as HTMLButtonElement).disabled).toBe(true);
 await waitFor(()=>expect(request).toHaveBeenCalled());
 expect(JSON.parse(vi.mocked(request).mock.calls[0][1]!.body as string)).toEqual(rawProcessing);
 fireEvent.change(fields[0],{target:{value:'30'}});fireEvent.change(fields[1],{target:{value:'1500.5'}});fireEvent.change(fields[2],{target:{value:'0'}});
 expect((screen.getByText('Apply recipe') as HTMLButtonElement).disabled).toBe(false);
 fireEvent.click(screen.getByText('Apply recipe'));
 expect(onChange).toHaveBeenLastCalledWith({...rawProcessing,background:'rolling_ball',offsets:[0],radius_px:30,rolling_height:1500.5,sigma_px:0});
});
it('keeps cleared offsets blank and ignores an unused blank radius after changing methods',()=>{
 const onChange=vi.fn();render(<ProcessingPanel imageId="test" z={0} labels={['A']} bitDepth={16} value={rawProcessing} disabled={false} onChange={onChange}/>);
 fireEvent.change(screen.getByLabelText('Background method'),{target:{value:'opening'}});
 fireEvent.change(screen.getByLabelText('Background radius (XY pixels)'),{target:{value:''}});
 fireEvent.change(screen.getByLabelText('Background method'),{target:{value:'constant'}});
 const offset=screen.getByLabelText('A offset') as HTMLInputElement;
 fireEvent.change(offset,{target:{value:''}});expect(offset.value).toBe('');
 expect((screen.getByText('Apply recipe') as HTMLButtonElement).disabled).toBe(true);
 fireEvent.change(offset,{target:{value:'0'}});fireEvent.click(screen.getByText('Apply recipe'));
 expect(onChange).toHaveBeenLastCalledWith({...rawProcessing,background:'constant',offsets:[0]});
});
