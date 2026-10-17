import {useEffect,useState} from 'react';
import {json} from './api';
import {useProjectState} from './ProjectContext';
type Status={cleanup?:{freed_bytes:number};ready:boolean;running:boolean;verified:boolean;model_available:boolean;runtime_available:boolean;model:{name:string;bytes:number;license:string}};
type Reply={model?:{name:string};recorded_quantities?:{label:string;value:number;unit:string}[];answer:string;status:string;project_revision:number;elapsed_seconds:number;sources:{id:string;title:string;url?:string;response_sha256?:string}[];audit:{tool:string;result:unknown}[]};
type Turn={question:string;reply:Reply};
export function AssistantPanel({projectId}:{projectId:string|null}){
 const [status,setStatus]=useState<Status>(),[error,setError]=useState(''),[busy,setBusy]=useState(false),[question,setQuestion]=useState(''),[online,setOnline]=useState(false);
 const [turns,setTurns]=useProjectState<Turn[]>('AssistantPanel.turns',[]);
 async function refresh(){try{setStatus(await json<Status>('/api/assistant/status'));}catch(e){setError(String(e));}}
 useEffect(()=>{refresh();const timer=setInterval(refresh,5000);return()=>clearInterval(timer);},[]);
 async function control(action:'start'|'stop'){setBusy(true);setError('');try{setStatus(await json<Status>('/api/assistant/'+action,{method:'POST'}));}catch(e){setError(String(e));}finally{setBusy(false);}}
 async function ask(){if(!projectId||!question.trim())return;setBusy(true);setError('');const prompt=question.trim();
  try{const history=turns.slice(-2).flatMap(t=>[{role:'user',content:t.question},{role:'assistant',content:t.reply.answer}]);
   const reply=await json<Reply>('/api/assistant/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_id:projectId,message:prompt,history,allow_online:online})});setTurns(previous=>[...previous.slice(-19),{question:prompt,reply}]);setQuestion('');setOnline(false);
  }catch(e){setError(String(e));}finally{setBusy(false);}}
 return <section className="panel statistics assistant"><p className="eyebrow">LOCAL RESEARCH ASSISTANT · EXPERIMENTAL</p><h2>Interpret measurements with evidence</h2>
 <p className="hint">Save your project before asking about it. The assistant reads the last saved revision; images, measurements and conversations remain on this computer. Save again to retain this conversation. AI answers are drafts for review.</p>
 <div className="assistant-status" role="status">{status?`${status.model.name} · ${(status.model.bytes/1e9).toFixed(2)} GB model · ${status.ready?'Ready':status.running?'Loading model…':status.model_available&&status.runtime_available?'Available locally':'Local model/runtime not installed'}`:'Checking local model…'}</div>
 {(status?.cleanup?.freed_bytes??0)>0&&<p className="hint">Removed retired model files and temporary downloads · {(status!.cleanup!.freed_bytes/1e9).toFixed(2)} GB recovered.</p>}
 <div className="roi-tools"><button disabled={busy||!status?.model_available||!status?.runtime_available||status.running} onClick={()=>control('start')}>Start local model</button><button className="secondary" disabled={busy||!status?.running} onClick={()=>control('stop')}>Unload model</button></div>
 {!status?.model_available&&<p className="hint">The pinned model and runtime are separate from this development application. Setup and size details are in docs/LOCAL_ASSISTANT.md. No cloud LLM or subscription is used.</p>}
 {!projectId&&<p className="volume-warning">Save a project using the controls above to enable project questions.</p>}
 <label>Ask about the saved project<textarea aria-label="Ask the local assistant" rows={4} maxLength={3000} disabled={busy} value={question} onChange={e=>setQuestion(e.target.value)} placeholder="What do my ROI results support, and what controls are missing?"/></label>
 <label className="check-label"><input type="checkbox" checked={online} disabled={busy} onChange={e=>setOnline(e.target.checked)}/> Allow repeating the exact saved STRING/KEGG query online for this question. Only its identifiers and lookup settings leave this computer.</label>
 <p className="hint">Academic-use acknowledgement and offline-only settings in Molecular evidence still apply. Otherwise the assistant uses saved results and cached evidence only.</p>
 <button disabled={busy||!projectId||!status?.ready||!question.trim()} onClick={ask}>{busy?'Working locally…':'Ask local assistant'}</button>{turns.length>0&&<button className="secondary" disabled={busy} onClick={()=>setTurns([])}>Clear conversation</button>}
 {error&&<p role="alert" className="error">{error}</p>}
 <div className="assistant-conversation">{turns.map((turn,index)=><article key={index} className="assistant-turn"><h3>{turn.question}</h3><p className="assistant-answer">{turn.reply.answer}</p>{!!turn.reply.recorded_quantities?.length&&<details><summary>Recorded quantities · from the saved analysis</summary><div className="table-scroll"><table><thead><tr><th>Quantity</th><th>Recorded value</th></tr></thead><tbody>{turn.reply.recorded_quantities.map((fact,i)=><tr key={i}><td>{fact.label.replace(/pixel_count/g,'pixel count').replace(/area_um2/g,'area').replace(/thresholded_m1/g,'thresholded Manders M1').replace(/thresholded_m2/g,'thresholded Manders M2').replace(/pcc/g,'Pearson r').replace(/spearman/g,'Spearman ρ')}</td><td>{Number(fact.value.toPrecision(6))} {fact.unit}</td></tr>)}</tbody></table></div></details>}<p className="hint">{turn.reply.model?.name??'Earlier assistant model'} · {turn.reply.status} · saved revision {turn.reply.project_revision} · {turn.reply.elapsed_seconds}s</p>
 {turn.reply.sources.map(source=><p className="hint" key={source.id}>[{source.id}] {source.url?<a href={source.url} target="_blank" rel="noreferrer">{source.title}</a>:source.title}</p>)}
 <details><summary>Application tool record · {turn.reply.audit.length} calls</summary>{turn.reply.audit.map((entry,i)=><details key={i}><summary>{entry.tool}</summary><pre>{JSON.stringify(entry.result,null,2)}</pre></details>)}</details></article>)}</div>
 <p className="validation-note">Colocalization alone does not establish molecular binding, pathway activation or a causal knockdown effect. Hypothetical scenarios require experimental validation. The assistant cannot alter measurements or analysis settings.</p></section>;
}
