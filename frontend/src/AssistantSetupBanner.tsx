import {useEffect,useState} from 'react';
import {json} from './api';
type Setup={phase:string;received_bytes:number;total_bytes:number;error:string|null;automatic:boolean;runtime_bundled:boolean};
export function AssistantSetupBanner(){
 const [setup,setSetup]=useState<Setup>(),[error,setError]=useState('');
 useEffect(()=>{let active=true;async function poll(){try{const status=await json<{setup?:Setup}>('/api/assistant/status');if(active)setSetup(status.setup);}catch{/* Main application reports service failures. */}}void poll();const timer=setInterval(poll,2000);return()=>{active=false;clearInterval(timer);};},[]);
 if(!setup||!setup.automatic||setup.phase==='complete')return null;
 const busy=['preparing','downloading','verifying'].includes(setup.phase);
 async function action(pause:boolean){try{setError('');await json('/api/assistant/install'+(pause?'/pause':''),{method:'POST'});}catch(e){setError(String(e));}}
 return <section className="assistant-setup" aria-label="Local assistant setup"><strong>Gemma local assistant · {setup.phase==='verifying'?'checking download integrity':setup.phase}</strong>
 <p>Setting up the local assistant requires a one-time {(setup.total_bytes/1e9).toFixed(2)} GB download. Image analysis remains available. Images, measurements and conversations are not uploaded. After setup, Gemma works offline.</p>
 <progress aria-label="Gemma download progress" max={setup.total_bytes} value={setup.received_bytes}/><span> {(setup.received_bytes/1e9).toFixed(2)} / {(setup.total_bytes/1e9).toFixed(2)} GB</span>
 <button className="secondary" onClick={()=>void action(busy)}>{busy?'Pause setup':'Resume setup'}</button>
 {(setup.error||error)&&<p role="status">{error||setup.error}</p>}</section>;
}
