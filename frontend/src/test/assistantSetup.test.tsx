import {it,expect,vi,afterEach} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor} from '@testing-library/react';
import {AssistantSetupBanner} from '../AssistantSetupBanner';
import {json} from '../api';
vi.mock('../api',()=>({json:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
it('shows download size and progress without blocking image analysis and allows pause',async()=>{
 vi.mocked(json).mockResolvedValue({setup:{phase:'downloading',received_bytes:1024,total_bytes:6975879296,automatic:true,runtime_bundled:true,error:null}});
 render(<AssistantSetupBanner/>);await screen.findByText(/one-time 6.98 GB/);
 fireEvent.click(screen.getByText('Pause setup'));
 await waitFor(()=>expect(vi.mocked(json)).toHaveBeenCalledWith('/api/assistant/install/pause',{method:'POST'}));
});
it('can resume paused setup and does not implicitly issue a download request',async()=>{
 vi.mocked(json).mockResolvedValue({setup:{phase:'paused',received_bytes:100,total_bytes:6975879296,automatic:true,runtime_bundled:true,error:'Setup paused'}});
 render(<AssistantSetupBanner/>);await screen.findByText('Resume setup');
 expect(vi.mocked(json).mock.calls.every(c=>c[0]==='/api/assistant/status')).toBe(true);
 fireEvent.click(screen.getByText('Resume setup'));
 await waitFor(()=>expect(vi.mocked(json)).toHaveBeenCalledWith('/api/assistant/install',{method:'POST'}));
});
it('keeps development setup optional',async()=>{
 vi.mocked(json).mockResolvedValue({setup:{phase:'idle',automatic:false}});const view=render(<AssistantSetupBanner/>);
 await waitFor(()=>expect(json).toHaveBeenCalled());expect(view.container.textContent).toBe('');
});
