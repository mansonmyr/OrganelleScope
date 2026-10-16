import {useEffect,useRef,useState} from 'react';
export interface PathwayDiagramData {pathway_id:string;image_data_url:string;width:number;height:number;source:{source_url:string;retrieved_utc:string;response_sha256:string;cached:boolean;stale:boolean};pathway_url:string;terms_url:string;interpretation:string}
export function PathwayDiagram({diagram,onClose}:{diagram:PathwayDiagramData;onClose:()=>void}){
 const dialog=useRef<HTMLDialogElement>(null),[scale,setScale]=useState(0);
 useEffect(()=>{dialog.current?.showModal();},[]);
 return <dialog ref={dialog} className="pathway-dialog" aria-labelledby="pathway-diagram-title" onClose={onClose}>
 <div className="pathway-dialog-header"><div><p className="eyebrow">KEGG · HUMAN REFERENCE PATHWAY</p><h2 id="pathway-diagram-title">Pathway diagram · {diagram.pathway_id}</h2></div><button autoFocus onClick={()=>dialog.current?.close()}>Close diagram</button></div>
 <p className="hint">{diagram.interpretation}</p><div className="pathway-tools"><label>Diagram zoom<select aria-label="Diagram zoom" value={scale} onChange={e=>setScale(Number(e.target.value))}><option value={0}>Fit entire map</option>{[50,75,100,125,150,200].map(n=><option key={n} value={n}>{n}%</option>)}</select></label><a href={diagram.pathway_url} target="_blank" rel="noreferrer">Open interactive map on KEGG</a></div>
 <div className="pathway-image-scroll" tabIndex={0} aria-label="Scrollable pathway diagram"><img src={diagram.image_data_url} alt={`KEGG human pathway diagram ${diagram.pathway_id}`} style={scale===0?{width:'auto',maxWidth:'100%',maxHeight:'50vh'}:{width:diagram.width*scale/100,maxWidth:'none'}}/></div>
 <p className="hint">Source: KEGG · retrieved {diagram.source.retrieved_utc} · {diagram.source.cached?'cached':'online'}{diagram.source.stale?' · stale':''}. Native image: {diagram.width} × {diagram.height}. Scroll to pan.</p><p><a href={diagram.source.source_url} target="_blank" rel="noreferrer">Original diagram</a> · <a href={diagram.terms_url} target="_blank" rel="noreferrer">Academic access terms</a></p>
 </dialog>;
}
