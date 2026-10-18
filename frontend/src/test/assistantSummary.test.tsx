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
it('shows incomplete question coverage separately from the answer and source review',async()=>{
 vi.mocked(json).mockImplementation(async path=>path==='/api/assistant/status'?{ready:true,model_available:true,runtime_available:true,model:{name:'Gemma',bytes:6975879296}}:{...summary,response_mode:'generated_draft',question_coverage:{assessed:true,all_parts_addressed:false,limitations:'Same-model review.',parts:[{index:0,request:'Why is this undefined?',status:'addressed',answer_quote:'The reference is empty.'},{index:1,request:'Is it absent from the cell?',status:'unanswered',answer_quote:''}]}});
 render(<AssistantPanel projectId={null}/>);fireEvent.change(screen.getByLabelText('Ask the local assistant'),{target:{value:'Why is this undefined? Is it absent from the cell?'}});fireEvent.click(screen.getByText('Ask local assistant'));
 await screen.findByText('Question coverage · automatic');expect(screen.getByText('unanswered')).toBeTruthy();expect(screen.getByText(/Some identified parts may be incomplete/)).toBeTruthy();
});
