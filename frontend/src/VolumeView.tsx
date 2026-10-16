import {useProjectState} from './ProjectContext';
import { useEffect, useRef, useState } from "react";
import type { ImageRecord } from "./api";
import { request } from "./api";
import { interleaveChannels, volumeSampleDistance } from "./volumeData";

type Controls = { cutoff: number; opacity: number; stretch: number };
const colors = [[1,.2,.35],[.15,1,.65],[.3,.5,1],[.9,.9,.9]];

export function VolumeView({ image, channel, onChannelChange }: {
  image: ImageRecord; channel: number; onChannelChange: (channel: number) => void
}) {
  const container = useRef<HTMLDivElement>(null);
  const apply = useRef<((settings: Controls) => void) | null>(null);
  const resetCamera = useRef<(() => void) | null>(null);
  const [message, setMessage] = useState("Loading 3D volume…");
  const [geometry, setGeometry] = useState("");
  const [cutoff, setCutoff] = useProjectState('VolumeView.cutoff',10);
  const [opacity, setOpacity] = useProjectState('VolumeView.opacity',35);
  const [stretch, setStretch] = useProjectState('VolumeView.stretch',1);
  const settings = useRef<Controls>({cutoff,opacity,stretch});
  settings.current={cutoff,opacity,stretch};
  const physical = ['X','Y','Z'].every(a=>image.info.calibration[a].value_um!=null);
  useEffect(()=>{apply.current?.({cutoff,opacity,stretch});},[cutoff,opacity,stretch]);
  useEffect(() => {
    const abort = new AbortController(); let dispose: (()=>void) | undefined;
    apply.current=null;resetCamera.current=null;
    setMessage("Loading 3D volume…"); setGeometry("");
    async function load() {
      try {
        const indices = channel === -1 ? Array.from({length:image.info.dimensions.C},(_,i)=>i) : [channel];
        const payloads = await Promise.all(indices.map(async c=>{
          const response = await request(`/api/images/${image.id}/volume?channel=${c}&units=${physical?'physical':'voxel'}`, { signal: abort.signal });
          return {channel:c,shape:JSON.parse(response.headers.get('X-Volume-Shape')!) as number[],
            spacing:JSON.parse(response.headers.get('X-Volume-Spacing')!) as number[],values:new Uint16Array(await response.arrayBuffer())};
        }));
        await import("@kitware/vtk.js/Rendering/Profiles/Volume");
        const [generic, imageData, dataArray, volume, volumeMapper, colorTransfer, piecewise] = await Promise.all([
          import("@kitware/vtk.js/Rendering/Misc/GenericRenderWindow"),
          import("@kitware/vtk.js/Common/DataModel/ImageData"),
          import("@kitware/vtk.js/Common/Core/DataArray"),
          import("@kitware/vtk.js/Rendering/Core/Volume"),
          import("@kitware/vtk.js/Rendering/Core/VolumeMapper"),
          import("@kitware/vtk.js/Rendering/Core/ColorTransferFunction"),
          import("@kitware/vtk.js/Common/DataModel/PiecewiseFunction")
        ]);
        if (abort.signal.aborted || !container.current) return;
        const window = generic.default.newInstance({ background: [.02,.04,.055], listenWindowResize: false });
        const renderer=window.getRenderer();
        const observer = new ResizeObserver(()=>window.resize());
        const cleanups: (()=>void)[]=[];
        dispose=()=>{observer.disconnect();cleanups.forEach(fn=>fn());window.delete();};
        window.setContainer(container.current);
        let previousStretch=settings.current.stretch;
        const {shape,spacing}=payloads[0];
        if(payloads.some(p=>JSON.stringify(p.shape)!==JSON.stringify(shape)||JSON.stringify(p.spacing)!==JSON.stringify(spacing)))throw new Error('Channel geometries do not match.');
        const source=imageData.default.newInstance();
        source.setDimensions(shape[2],shape[1],shape[0]);source.setSpacing(spacing);
        const values=interleaveChannels(payloads.map(p=>p.values));
        const scalars=dataArray.default.newInstance({name:'Native channels',values,numberOfComponents:payloads.length});
        source.getPointData().setScalars(scalars);
        const mapper=volumeMapper.default.newInstance();mapper.setInputData(source);
        mapper.setSampleDistance(volumeSampleDistance(shape,spacing,settings.current.stretch));
        mapper.setMaximumSamplesPerRay(1000);
        const actor=volume.default.newInstance();actor.setMapper(mapper);
        actor.getProperty().setIndependentComponents(true);
        actor.getProperty().setInterpolationTypeToLinear();actor.getProperty().setShade(false);
        renderer.addVolume(actor);
        cleanups.push(()=>{renderer.removeVolume(actor);actor.delete();mapper.delete();source.delete();scalars.delete();});
        const components=payloads.map(({values,channel:c},component)=>{
          const ct=colorTransfer.default.newInstance();const op=piecewise.default.newInstance();
          const sorted=Array.from(values.filter((v,i)=>v>0 && i%8===0)).sort((a,b)=>a-b);
          const high=sorted[Math.floor((sorted.length-1)*.995)] || values.reduce((a,b)=>Math.max(a,b),1);
          const color=colors[c];
          ct.addRGBPoint(0,0,0,0);ct.addRGBPoint(high,...color as [number,number,number]);
          actor.getProperty().setRGBTransferFunction(component,ct);actor.getProperty().setScalarOpacity(component,op);
          actor.getProperty().setScalarOpacityUnitDistance(component,Math.min(...spacing));
          actor.getProperty().setComponentWeight(component,1);
          cleanups.push(()=>{ct.delete();op.delete();});
          return {op,high};
        });
        function frame() {
          const bounds=actor.getBounds();
          const center=[(bounds[0]+bounds[1])/2,(bounds[2]+bounds[3])/2,(bounds[4]+bounds[5])/2];
          const size=Math.max(bounds[1]-bounds[0],bounds[3]-bounds[2],bounds[5]-bounds[4],1);
          const camera=renderer.getActiveCamera();
          camera.setFocalPoint(center[0],center[1],center[2]);
          camera.setPosition(center[0]+size,center[1]-size,center[2]+size*.8);camera.setViewUp(0,0,1);
          renderer.resetCamera();renderer.resetCameraClippingRange();window.getRenderWindow().render();
        }
        resetCamera.current=frame;
        apply.current=({cutoff,opacity,stretch})=>{
          for(const {op,high} of components){
            op.removeAllPoints();op.addPoint(0,0);op.addPoint(high*cutoff/100,0);op.addPoint(high,opacity/100);
          }
          actor.setScale(1,1,stretch);
          mapper.setSampleDistance(volumeSampleDistance(shape,spacing,stretch));
          if(stretch!==previousStretch){previousStretch=stretch;frame();}
          else window.getRenderWindow().render();
        };
        apply.current(settings.current);
        observer.observe(container.current);window.resize();frame();
        setGeometry(`${shape[2]} × ${shape[1]} × ${shape[0]} display voxels · spacing ${spacing.map(v=>v.toFixed(3)).join(' × ')} ${physical?'µm':'source voxel steps'} · ${indices.length} channel${indices.length>1?'s':''}`);
        setMessage(payloads.every(p=>p.values.every(v=>v===0))?'The selected channels contain only zero intensity.':'');
      } catch(e) { if (!abort.signal.aborted) {dispose?.();dispose=undefined;apply.current=null;resetCamera.current=null;setMessage(`3D preview unavailable: ${String(e)}`);} }
    }
    void load();
    return () => { abort.abort();apply.current=null;resetCamera.current=null;dispose?.(); };
  }, [image, channel, physical]);
  return <div><div className="volume-controls"><label>3D channels<select aria-label="3D channels" value={channel} onChange={e=>onChannelChange(Number(e.target.value))}><option value={-1}>All channels</option>{image.info.channel_labels.map((name,i)=><option key={i} value={i}>{name}</option>)}</select></label><p className="hint">Drag to rotate · Scroll to zoom<br/>{physical?'Calibrated physical proportions':'Voxel-space preview · physical scale unknown'}</p><button onClick={()=>resetCamera.current?.()}>Reset 3D view</button></div>
    {!physical && <p className="volume-warning">X, Y or Z spacing is unknown. This preview uses pixel and slice counts, not physical dimensions. Confirm calibration for reliable physical proportions and distances.</p>}
    <div className="volume-settings"><label>Background cutoff: {cutoff}%<input aria-label="3D background cutoff" type="range" min="0" max="95" value={cutoff} onChange={e=>setCutoff(Number(e.target.value))}/></label><label>Opacity: {opacity}%<input aria-label="3D opacity" type="range" min="1" max="100" value={opacity} onChange={e=>setOpacity(Number(e.target.value))}/></label><label>Display Z stretch: {stretch}×<select aria-label="Display Z stretch" value={stretch} onChange={e=>setStretch(Number(e.target.value))}>{[1,2,5,10].map(v=><option key={v} value={v}>{v}×{v===1?(physical?' (true proportions)':' (voxel proportions)'):' (exaggerated display)'}</option>)}</select></label></div>
    {stretch!==1 && <p className="volume-warning">Z is stretched {stretch}× for visibility only. This view exaggerates depth; source data, calibration and measurements are unchanged.</p>}
    {message && <p role="status" className="volume-error">{message}</p>}<div className="volume-canvas" aria-label="Interactive 3D volume" ref={container}/>
    <p className="hint viewer-note">{geometry}<br/>Display controls affect visualization only. Preview spacing includes the downsampling step; source calibration stays unchanged. The preview is downsampled; full-resolution source pixels remain unchanged. This is volume visualization, not super-resolution reconstruction.</p></div>;
}
