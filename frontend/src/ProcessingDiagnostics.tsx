import {useEffect,useRef,useState} from 'react';
import {json} from './api';
import type {ProcessingConfig} from './ProcessingPanel';
import {downloadReport,formatMetric as fmt} from './reportDownload';
export function ProcessingDiagnostics({imageId,z,config}:{imageId:string;z:number;config:ProcessingConfig}){
 const [report,setReport]=useState<Record<string,any>>(),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const pending=useRef<AbortController>();
 useEffect(()=>{pending.current?.abort();setBusy(false);setReport(undefined);setError('');return()=>pending.current?.abort();},[imageId,z,config]);
 async function run(){pending.current?.abort();const abort=new AbortController();pending.current=abort;setBusy(true);setError('');try{const result=await json<Record<string,any>>(`/api/images/${imageId}/processing/diagnostics?z=${z}`,{signal:abort.signal,method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});if(!abort.signal.aborted)setReport(result);}catch(e){if(!abort.signal.aborted)setError(String(e));}finally{if(!abort.signal.aborted)setBusy(false);}}
 return <div><button disabled={busy} onClick={run}>{busy?'Measuring changes…':'Measure processing changes'}</button>{error&&<p role="alert">{error}</p>}{report&&<><div className="table-scroll"><table><caption>Applied recipe · full XY plane · Z {z+1}</caption><thead><tr><th>Channel</th><th>Raw mean</th><th>Processed mean</th><th>Net intensity removed (%)</th><th>Residual RMSE</th><th>Changed pixels</th><th>Residual X / Y correlation</th></tr></thead><tbody>{report.channels.map((r:Record<string,any>)=><tr key={r.channel}><td>{r.label}</td><td>{fmt(r.raw_mean)}</td><td>{fmt(r.processed_mean)}</td><td>{fmt(r.net_removed_percent)}</td><td>{fmt(r.residual_rmse)}</td><td>{fmt(r.changed_pixels)}</td><td>{fmt(r.residual_neighbor_correlation_x)} / {fmt(r.residual_neighbor_correlation_y)}</td></tr>)}</tbody></table></div><p className="hint">{report.scope}</p><button onClick={()=>downloadReport(report,'OrganelleScope-processing-diagnostics.json')}>Export processing changes</button></>}</div>;
}
