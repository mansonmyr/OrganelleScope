import {useEffect,useState} from 'react';
import type {AreaROI} from './RoiOverlay';
export function CircleSizeEditor({roi,sx,sy,width,height,disabled,onChange}:{roi:AreaROI;sx:number|null;sy:number|null;width:number;height:number;disabled:boolean;onChange:(roi:AreaROI)=>void}){
 const calibrated=sx!=null&&sy!=null&&sx>0&&sy>0;
 const radius=Math.hypot(roi.points[1].x-roi.points[0].x,roi.points[1].y-roi.points[0].y);
 const current=roi.diameter_um??(calibrated?2*radius*sx!:null);
 const [value,setValue]=useState(current==null?'':String(Number(current.toPrecision(8)))),[error,setError]=useState('');
 useEffect(()=>{setValue(current==null?'':String(Number(current.toPrecision(8))));setError('');},[roi,sx,sy]);
 const d=Number(value),rx=calibrated?d/(2*sx!):0,ry=calibrated?d/(2*sy!):0,c=roi.points[0];
 const clipped=d>0&&(c.x-rx<0||c.y-ry<0||c.x+rx>width-1||c.y+ry>height-1);
 function apply(){if(!calibrated||!Number.isFinite(d)||d<=0){setError('Enter a positive finite diameter with valid X/Y calibration.');return;}
 onChange({...roi,diameter_um:d,points:[c,{x:c.x+rx,y:c.y}]});setError('');}
 return <div className="circle-size"><label>Diameter (µm)<input aria-label={`Diameter in micrometers for ${roi.id}`} type="number" min="0" step="any" value={value} disabled={disabled||!calibrated} onChange={e=>setValue(e.target.value)}/></label><button className="secondary" disabled={disabled||!calibrated} onClick={apply}>Apply diameter</button>
 {!calibrated&&<span className="hint">Set X/Y calibration to enter a physical diameter.</span>}
 {calibrated&&roi.diameter_um==null&&sx!==sy&&<span className="hint">This pixel circle spans {(2*radius*sx!).toPrecision(4)} × {(2*radius*sy!).toPrecision(4)} µm. Applying a diameter makes it physically circular.</span>}
 {clipped&&<span className="hint">Extends beyond the image; only the intersection will be measured.</span>}{error&&<span role="alert">{error}</span>}</div>;
}
