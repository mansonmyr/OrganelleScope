import {it,expect,vi,afterEach} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor} from '@testing-library/react';
import {AssistantPanel} from '../AssistantPanel';
import {json} from '../api';
vi.mock('../api',()=>({json:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
const summary={response_mode:'application_summary',answer:'Recorded analysis summary.',model:null,report_findings:['Both proximity directions are already calculated.'],project_revision:null,context_kind:'workspace',elapsed_seconds:0,status:'Application summary',interpretation_notes:['A recorded channel is constant.'],recorded_quantities:[{label:'pixel_count',value:25,unit:'pixels'}],sources:[],audit:[]};
it('shows application notes without a model or project and keeps a failed question for retry',async()=>{
 vi.mocked(json).mockImplementation(async(path)=>path==='/api/assistant/status'?{ready:false,model_available:false,runtime_available:false,model:{name:'Gemma',bytes:6975879296}}:path==='/api/assistant/notes'?summary:{...summary,generation_error:'Draft withheld.'});
 render(<AssistantPanel projectId={null}/>);
 fireEvent.click(screen.getByText('Show recorded analysis summary'));
 await screen.findByText('A recorded channel is constant.');expect(screen.getByText('Both proximity directions are already calculated.')).toBeTruthy();expect(screen.getByText('25 pixels')).toBeTruthy();
 expect(vi.mocked(json).mock.calls.some(c=>c[0]==='/api/assistant/start')).toBe(false);
 fireEvent.change(screen.getByLabelText('Ask the local assistant'),{target:{value:'What does this result mean?'}});
 fireEvent.click(screen.getByText('Ask local assistant'));
 await waitFor(()=>expect(screen.getByText(/AI draft unavailable/)).toBeTruthy());
 expect((screen.getByLabelText('Ask the local assistant') as HTMLTextAreaElement).value).toBe('What does this result mean?');
});
