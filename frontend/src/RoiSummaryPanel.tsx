import type {AnalysisResult} from './StatisticsPanel';
import {formatMetric as fmt} from './reportDownload';
export function RoiSummaryPanel({analysis}:{analysis:AnalysisResult}){
 return <section className="panel statistics"><p className="eyebrow">ROI INTENSITY MEASUREMENTS</p><h2>Measured regions</h2><p className="hint">{analysis.scope} Channel associations are shown in their separate workspace.</p>{analysis.results.map((r,i)=><article key={r.roi.id}><h3>ROI {i+1} · {r.roi.kind} · Z {r.roi.z+1}</h3><p>{r.pixel_count.toLocaleString()} pixels · area {fmt(r.area_um2)} µm²</p><div className="table-scroll"><table><thead><tr><th>Channel</th><th>Mean</th><th>Sum</th><th>SD</th></tr></thead><tbody>{r.channel_summary.map(c=><tr key={c.label}><td>{c.label}</td><td>{fmt(c.mean)}</td><td>{fmt(c.sum)}</td><td>{fmt(c.std)}</td></tr>)}</tbody></table></div>{r.warnings.map(w=><p className="hint" key={w}>{w}</p>)}</article>)}</section>;
}
