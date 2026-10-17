import {useId,useRef} from 'react';
import {formatMetric} from './reportDownload';
export function MetricValue({value,reason,label}:{value:number|null|undefined;reason?:string;label:string}){
 const dialog=useRef<HTMLDialogElement>(null),id=useId();
 if(value!=null)return <>{formatMetric(value)}</>;
 return <><button className="metric-explanation" aria-label={`Why ${label} is unavailable`} title={reason??'Recalculate this older report for a metric-specific explanation.'} onClick={()=>dialog.current?.showModal()}>Unavailable ⓘ</button><dialog ref={dialog} className="calibration-dialog" aria-labelledby={id}><h2 id={id}>{label}: unavailable</h2><p>{reason??'This older report did not record a metric-specific reason. Recalculate it with the current version and inspect channel intensities and threshold status.'}</p><p>Unavailable is distinct from a measured zero. Check the selected channels, source data, region and preparation settings. An empty image channel does not establish biological absence.</p><form method="dialog"><button autoFocus>Close metric explanation</button></form></dialog></>;
}


export function metricReason(key:string,pair:{label_a:string;label_b:string;channel_a?:number;channel_b?:number;unavailable_reasons?:Record<string,string>;thresholds?:{status:string;a:number|null;b:number|null}},channels:{label:string;sum:number;std:number}[]):string|undefined{
 if(pair.unavailable_reasons?.[key])return pair.unavailable_reasons[key];
 const byLabel=(label:string)=>{const matches=channels.filter(c=>c.label===label);return matches.length===1?matches[0]:undefined;};
 const a=pair.channel_a!=null?channels[pair.channel_a]:byLabel(pair.label_a),b=pair.channel_b!=null?channels[pair.channel_b]:byLabel(pair.label_b);
 if((key==='pcc'||key==='spearman')&&[a,b].some(c=>c?.std===0))return [a,b].filter(c=>c?.std===0).map(c=>`${c!.label} ${c!.sum===0?'contains only zero intensities':'has constant intensity'} in the measured region`).join('; ')+'. Correlation is undefined because the normalization denominator is zero.';
 if(key==='moc'&&(a?.sum===0||b?.sum===0))return 'Overlap is undefined because at least one channel has zero intensity energy in this region.';
 if(key.startsWith('thresholded_')&&pair.thresholds&&pair.thresholds.a==null)return 'Automatic thresholds were not obtained. No fallback threshold is substituted.';
 const channel=key==='m1'||key==='thresholded_m1'?a:key==='m2'||key==='thresholded_m2'?b:undefined;
 if(channel?.sum===0)return `${key} is undefined because ${channel.label} has zero summed intensity (zero denominator).`;
 return undefined;
}
