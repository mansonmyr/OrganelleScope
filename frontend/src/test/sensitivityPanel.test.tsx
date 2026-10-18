import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {SensitivityPanel} from '../SensitivityPanel';
import {json,type ImageRecord} from '../api';
vi.mock('../api',()=>({json:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
it('requires explicit thresholds, permits blank editing and sends only declared perturbations',async()=>{
 const image={id:'image',info:{bit_depth:16}} as ImageRecord;
 const base={rois:[{id:'r'}],threshold_mode:'costes'};
 const view=render(<SensitivityPanel image={image} base={base} mode="roi"/>);
 fireEvent.click(screen.getByText('ROI size & threshold sensitivity'));
 const run=screen.getByText('Run settings sensitivity') as HTMLButtonElement;expect(run.disabled).toBe(true);
 view.rerender(<SensitivityPanel image={image} base={{...base,threshold_mode:'manual',thresholds:[5,10]}} mode="roi"/>);
 const step=screen.getByLabelText('Threshold step (native intensity)');fireEvent.change(step,{target:{value:''}});expect((step as HTMLInputElement).value).toBe('');expect(run.disabled).toBe(true);
 fireEvent.change(step,{target:{value:'20'}});vi.mocked(json).mockResolvedValue({results:[],scope:'Descriptive only'});fireEvent.click(run);
 await screen.findByText('Descriptive only');
 const body=JSON.parse(vi.mocked(json).mock.calls[0][1]!.body as string);expect(body.threshold_step).toBe(20);expect(body.size_fraction).toBe(.2);
});
it('clears a sweep when source settings change',async()=>{
 vi.mocked(json).mockResolvedValue({variants:[],scope:'Old sweep'});
 const image={id:'image',info:{bit_depth:16}} as ImageRecord;const base={method:'manual',exclude_labels:[],threshold:5};
 const view=render(<SensitivityPanel image={image} base={base} mode="volume"/>);
 fireEvent.click(screen.getByText('Cuboid boundary & threshold sensitivity'));fireEvent.click(screen.getByText('Run settings sensitivity'));await screen.findByText('Old sweep');
 view.rerender(<SensitivityPanel image={image} base={{...base,threshold:10}} mode="volume"/>);
 await waitFor(()=>expect(screen.queryByText('Old sweep')).toBeNull());
});
