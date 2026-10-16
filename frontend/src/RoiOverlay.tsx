import { useRef, useState } from 'react';
import type { PointerEvent } from 'react';
import type { LineRoi } from './types';
export type Point = { x: number; y: number };
export type AreaROI = { id: string; kind: 'circle' | 'polygon'; z: number; points: Point[] };
export type DrawTool = 'line' | 'circle' | 'polygon';
export function RoiOverlay({ width, height, z, tool, rois, line, onLine, onAdd, disabled=false }: {
  disabled?: boolean; width: number; height: number; z: number; tool: DrawTool; rois: AreaROI[]; line: LineRoi | null;
  onLine: (line: LineRoi | null) => void; onAdd: (roi: AreaROI) => void;
}) {
  const svg = useRef<SVGSVGElement>(null);
  const [draft, setDraft] = useState<Point[]>([]);
  const drag = useRef<Point | null>(null);
  function point(e: PointerEvent<SVGSVGElement>): Point {
    const p = svg.current!.createSVGPoint(); p.x=e.clientX; p.y=e.clientY;
    const c=p.matrixTransform(svg.current!.getScreenCTM()!.inverse());
    return {x:Math.max(0,Math.min(width-1,c.x)), y:Math.max(0,Math.min(height-1,c.y))};
  }
  function add(points: Point[], kind: AreaROI['kind']) { onAdd({id:crypto.randomUUID(),kind,z,points}); setDraft([]); }
  const stroke = Math.max(1,width/400);
  function shape(points: Point[], kind: AreaROI['kind'], key: string, draft=false) {
    return kind==='circle' && points.length===2 ? <circle key={key} cx={points[0].x} cy={points[0].y} r={Math.hypot(points[1].x-points[0].x,points[1].y-points[0].y)} fill="#31d6a020" stroke="#31d6a0" strokeWidth={stroke}/> : <polygon key={key} points={points.map(p=>`${p.x},${p.y}`).join(' ')} fill="#31d6a020" stroke={draft?'#fff':'#31d6a0'} strokeWidth={stroke}/>;
  }
  return <><svg ref={svg} aria-label="ROI drawing surface" viewBox={`0 0 ${width} ${height}`}
    onPointerDown={e=>{ if(disabled || e.button!==0)return; const p=point(e); if(tool==='polygon'){setDraft(d=>[...d,p]);return;} drag.current=p;e.currentTarget.setPointerCapture(e.pointerId);if(tool==='line')onLine({start:p,end:p,sampleSpacingPx:1});else setDraft([p,p]); }}
    onPointerMove={e=>{if(!drag.current)return;const p=point(e);if(tool==='line')onLine({start:drag.current,end:p,sampleSpacingPx:1});else setDraft([drag.current,p]);}}
    onPointerUp={e=>{if(!drag.current)return;const p=point(e);if(tool==='circle' && Math.hypot(p.x-drag.current.x,p.y-drag.current.y)>0)add([drag.current,p],'circle');else if(tool==='line')onLine({start:drag.current,end:p,sampleSpacingPx:1});drag.current=null;if(e.currentTarget.hasPointerCapture(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId);}}
    onPointerCancel={()=>{drag.current=null;setDraft([]);}}>
    {rois.map((r,i)=>r.z===z?<g key={r.id}>{shape(r.points,r.kind,r.id)}<text x={r.points[0].x} y={r.points[0].y} fill="white" fontSize={width/40}>ROI {i+1}</text></g>:null)}
    {draft.length>0 && shape(draft,tool==='circle'?'circle':'polygon','draft',true)}
    {line && <line x1={line.start.x} y1={line.start.y} x2={line.end.x} y2={line.end.y} stroke="#fff" strokeWidth={stroke}/>}
  </svg>{tool==='polygon' && <div className="polygon-actions"><button disabled={disabled || draft.length<3} onClick={()=>add(draft,'polygon')}>Finish polygon ({draft.length})</button><button disabled={disabled} onClick={()=>setDraft([])}>Cancel polygon</button></div>}</>;
}
