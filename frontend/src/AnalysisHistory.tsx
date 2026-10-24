import {useEffect,useState} from 'react';
import {json} from './api';
import {downloadReport} from './reportDownload';
export function AnalysisHistory({imageId,reportId}:{imageId:string;reportId?:string}){
 const [rows,setRows]=useState<{sha256:string;algorithm_version?:string;created_utc?:string}[]>([]),[error,setError]=useState('');
 useEffect(()=>{const abort=new AbortController();setRows([]);setError('');json<typeof rows>(`/api/images/${imageId}/analysis-history`,{signal:abort.signal}).then(v=>{if(!abort.signal.aborted){if(Array.isArray(v))setRows(v);else{setRows([]);setError('The report history response could not be read. Existing reports are unchanged.');}}}).catch(e=>{if(!abort.signal.aborted)setError(String(e));});return()=>abort.abort();},[imageId,reportId]);
 async function exportReport(digest:string){try{const report=await json(`/api/images/${imageId}/analysis-history/${digest}`);downloadReport(report,`OrganelleScope-ROI-${digest.slice(0,12)}.json`);}catch(e){setError(String(e));}}
 return <details><summary>Preserved ROI reports ({rows.length})</summary><p className="hint">Recalculation retains the exact previous result. These exports preserve their original algorithm and settings; older reports may not contain current quality diagnostics.</p>{error&&<p role="alert">{error}</p>}{rows.map(r=><p key={r.sha256}>{r.algorithm_version??'Older report'} · {r.created_utc??'Date not recorded'} <button onClick={()=>exportReport(r.sha256)}>Export {r.sha256.slice(0,8)}</button></p>)}</details>;
}
