import {useEffect,useLayoutEffect,useRef,useState,type ReactNode,type CSSProperties,type PointerEvent} from 'react';
import {useProjectState} from './ProjectContext';
export function PreviewZoom({width,height,children}:{width:number;height:number;children:ReactNode}){
 const viewport=useRef<HTMLDivElement>(null),anchor=useRef<{x:number;y:number;clientX:number;clientY:number}>();
 const drag=useRef<{id:number;x:number;y:number;left:number;top:number}>();
 const space=useRef(false);
 const [pan,setPan]=useState(false),[dragging,setDragging]=useState(false);
 const [zoom,setZoom]=useProjectState('PreviewZoom.zoom',100),[size,setSize]=useState({width:650,height:450});
 const zoomRef=useRef(zoom);zoomRef.current=zoom;
 useEffect(()=>{const element=viewport.current!;const update=()=>{const width=element.clientWidth,height=element.clientHeight;if(width>0&&height>0)setSize({width,height});};update();if(typeof ResizeObserver==='undefined')return;const observer=new ResizeObserver(update);observer.observe(element);return()=>observer.disconnect();},[]);
 const fit=Math.min(size.width/width,size.height/height),scale=fit*zoom/100;
 function change(next:number,client?:{x:number;y:number}){
  const element=viewport.current!,stage=element.querySelector<HTMLElement>('.image-stage');
  const rect=element.getBoundingClientRect(),clientX=client?client.x-rect.left-element.clientLeft:element.clientWidth/2,clientY=client?client.y-rect.top-element.clientTop:element.clientHeight/2;
  if(stage&&stage.offsetWidth&&stage.offsetHeight)anchor.current={x:(element.scrollLeft+clientX-stage.offsetLeft)/stage.offsetWidth,y:(element.scrollTop+clientY-stage.offsetTop)/stage.offsetHeight,clientX,clientY};
  const value=Math.max(25,Math.min(800,Math.round(next)));zoomRef.current=value;setZoom(value);
 }
 // A native non-passive listener is needed to consume trackpad pinch (ctrl+wheel)
 // and wheel events without also zooming or scrolling the containing application.
 const changeRef=useRef(change);changeRef.current=change;
 useEffect(()=>{const element=viewport.current!;const wheel=(event:WheelEvent)=>{event.preventDefault();const delta=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?element.clientHeight:1);changeRef.current(zoomRef.current*Math.exp(-Math.max(-200,Math.min(200,delta))*(event.ctrlKey?0.01:0.002)),{x:event.clientX,y:event.clientY});};element.addEventListener('wheel',wheel,{passive:false});return()=>element.removeEventListener('wheel',wheel);},[]);
 useLayoutEffect(()=>{const element=viewport.current,stage=element?.querySelector<HTMLElement>('.image-stage'),p=anchor.current;if(element&&stage&&p){element.scrollLeft=p.x*stage.offsetWidth+stage.offsetLeft-p.clientX;element.scrollTop=p.y*stage.offsetHeight+stage.offsetTop-p.clientY;anchor.current=undefined;}},[zoom,size]);
 function endDrag(e:PointerEvent<HTMLDivElement>){if(drag.current?.id!==e.pointerId)return;e.stopPropagation();drag.current=undefined;setDragging(false);if(e.currentTarget.hasPointerCapture?.(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId);}
 return <div className="preview-zoom"><div className="preview-zoom-controls" role="toolbar" aria-label="Preview zoom"><button aria-label="Zoom out XY preview" disabled={zoom<=25} onClick={()=>change(zoom-25)}>−</button><label>Zoom: {zoom}% of fit<input aria-label="XY preview zoom" type="range" min="25" max="800" step="1" value={zoom} onChange={e=>change(Number(e.target.value))}/></label><button aria-label="Zoom in XY preview" disabled={zoom>=800} onClick={()=>change(zoom+25)}>+</button><button onClick={()=>{anchor.current=undefined;zoomRef.current=100;setZoom(100);if(viewport.current){viewport.current.scrollLeft=0;viewport.current.scrollTop=0;}}}>Fit image</button><button aria-pressed={pan} onClick={()=>setPan(!pan)}>Pan image</button><span className="hint" id="xy-gesture-help">Pinch or scroll to zoom at the pointer. Enable Pan image to drag; switch it off to draw ROIs. Space-drag or middle-drag also pans. PNG captures the whole XY plane.</span></div><div className={`preview-scroll${pan?' pan-enabled':''}${dragging?' is-panning':''}`} ref={viewport} tabIndex={0} aria-label="Zoomable XY image" aria-describedby="xy-gesture-help"
 onKeyDown={e=>{if(e.code==='Space'){e.preventDefault();space.current=true;}}} onKeyUp={e=>{if(e.code==='Space'){e.preventDefault();space.current=false;}}} onBlur={()=>{space.current=false;}}
 onPointerDownCapture={e=>{if(e.button!==1&&!(e.button===0&&(pan||space.current)))return;e.preventDefault();e.stopPropagation();e.currentTarget.focus({preventScroll:true});e.currentTarget.setPointerCapture?.(e.pointerId);drag.current={id:e.pointerId,x:e.clientX,y:e.clientY,left:e.currentTarget.scrollLeft,top:e.currentTarget.scrollTop};setDragging(true);}}
 onPointerMoveCapture={e=>{const p=drag.current;if(!p||p.id!==e.pointerId)return;e.preventDefault();e.stopPropagation();e.currentTarget.scrollLeft=p.left+p.x-e.clientX;e.currentTarget.scrollTop=p.top+p.y-e.clientY;}}
 onPointerUpCapture={endDrag} onPointerCancelCapture={endDrag} onLostPointerCapture={()=>{drag.current=undefined;setDragging(false);}}
 style={{'--preview-width':`${width*scale}px`,'--preview-height':`${height*scale}px`} as CSSProperties}>{children}</div></div>;
}
