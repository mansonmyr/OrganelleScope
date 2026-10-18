import {it,expect,vi,afterEach} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor} from '@testing-library/react';
import {ChannelPanel} from '../ChannelPanel';
import {json,type ImageRecord} from '../api';
vi.mock('../api',()=>({json:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
const image={id:'test',sha256:'source',info:{channel_labels:['A','B'],dimensions:{C:2,T:1},needs_axis_confirmation:false}} as unknown as ImageRecord;
it('preserves native channel order, blocks duplicates and submits expected metadata',async()=>{
 const updated={...image,info:{...image.info,channel_labels:['Marker A','B']}};vi.mocked(json).mockResolvedValue(updated);const onUpdate=vi.fn();
 render(<ChannelPanel image={image} z={1} disabled={false} onUpdate={onUpdate}/>);
 fireEvent.change(screen.getByLabelText('Channel 1 name'),{target:{value:'B'}});expect((screen.getByText('Apply channel names') as HTMLButtonElement).disabled).toBe(true);
 fireEvent.change(screen.getByLabelText('Channel 1 name'),{target:{value:'Marker A'}});fireEvent.click(screen.getByText('Apply channel names'));
 await waitFor(()=>expect(onUpdate).toHaveBeenCalledWith(updated));
 expect(JSON.parse(vi.mocked(json).mock.calls[0][1]!.body as string)).toEqual({labels:['Marker A','B'],expected_image_info:image.info});
});
it('shows selected-plane quality scope without treating storage counts as detector saturation',async()=>{
 vi.mocked(json).mockResolvedValue({z:1,scope:'Selected plane only',channels:[{channel:0,label:'A',min:0,max:4095,zero_pixels:3,pixel_count:20,storage_ceiling:65535,storage_ceiling_pixels:0,notes:[]}],calibration_notes:['X sampling unknown']});
 render(<ChannelPanel image={image} z={1} disabled={false} onUpdate={vi.fn()}/>);fireEvent.click(screen.getByText('Check selected-plane signal'));
 await screen.findByText('Selected plane only');expect(vi.mocked(json).mock.calls[0][0]).toBe('/api/images/test/quality?z=1');
 expect(screen.getByText(/clipping below the storage ceiling/)).toBeTruthy();
});
it('sends optional nominal resolution and detector ceiling without inserting zero into cleared values',async()=>{
 vi.mocked(json).mockResolvedValue({z:0,scope:'Selected plane only',channels:[],calibration_notes:[]});
 render(<ChannelPanel image={image} z={0} disabled={false} onUpdate={vi.fn()}/>);
 fireEvent.click(screen.getByText('Optional acquisition specifications'));
 const lateral=screen.getByLabelText('Lateral resolution (µm)');fireEvent.change(lateral,{target:{value:'.25'}});fireEvent.change(lateral,{target:{value:''}});expect((lateral as HTMLInputElement).value).toBe('');
 fireEvent.change(lateral,{target:{value:'.3'}});fireEvent.change(screen.getByLabelText('Detector ceiling (native intensity)'),{target:{value:'4095'}});fireEvent.click(screen.getByText('Check selected-plane signal'));
 await waitFor(()=>expect(json).toHaveBeenCalled());
 const query=new URL(String(vi.mocked(json).mock.calls[0][0]),'http://localhost').searchParams;expect(Number(query.get('lateral_resolution_um'))).toBe(.3);expect(Number(query.get('detector_ceiling'))).toBe(4095);
});
