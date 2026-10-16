import { useEffect, useRef, useState } from "react";
import type { ImageRecord } from "./api";
import { request } from "./api";

export function VolumeView({ image, channel, onChannelChange }: {
  image: ImageRecord; channel: number; onChannelChange: (channel: number) => void
}) {
  const container = useRef<HTMLDivElement>(null);
  const [message, setMessage] = useState("Loading calibrated volume…");
  const [geometry, setGeometry] = useState("");
  useEffect(() => {
    const abort = new AbortController(); let dispose: (()=>void) | undefined;
    setMessage("Loading calibrated volume…"); setGeometry("");
    async function load() {
      try {
        const response = await request(`/api/images/${image.id}/volume?channel=${channel}`, { signal: abort.signal });
        const shape: number[] = JSON.parse(response.headers.get("X-Volume-Shape")!);
        const spacing: number[] = JSON.parse(response.headers.get("X-Volume-Spacing")!);
        const values = new Uint16Array(await response.arrayBuffer());
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
        const source = imageData.default.newInstance();
        source.setDimensions(shape[2], shape[1], shape[0]); source.setSpacing(spacing);
        const scalars = dataArray.default.newInstance({ name: "Native intensity", values, numberOfComponents: 1 });
        source.getPointData().setScalars(scalars);
        const mapper = volumeMapper.default.newInstance(); mapper.setInputData(source);
        mapper.setSampleDistance(Math.min(...spacing) / 2);
        const actor = volume.default.newInstance(); actor.setMapper(mapper);
        const ct = colorTransfer.default.newInstance();
        const op = piecewise.default.newInstance();
        const sorted = Array.from(values.filter((_, i) => i % 8 === 0)).sort((a,b)=>a-b);
        const high = sorted[Math.floor((sorted.length-1)*.995)] || 1;
        const colors = [[1,.2,.35],[.15,1,.65],[.3,.5,1],[.9,.9,.9]];
        const color = colors[channel];
        ct.addRGBPoint(0,0,0,0); ct.addRGBPoint(high, color[0],color[1],color[2]);
        op.addPoint(0,0); op.addPoint(high*.1,0); op.addPoint(high,.65);
        actor.getProperty().setRGBTransferFunction(0,ct);
        actor.getProperty().setScalarOpacity(0,op);
        actor.getProperty().setScalarOpacityUnitDistance(0,Math.min(...spacing));
        actor.getProperty().setInterpolationTypeToLinear(); actor.getProperty().setShade(false);
        const observer = new ResizeObserver(()=>window.resize());
        dispose = () => { observer.disconnect(); window.getRenderer().removeVolume(actor); window.delete(); actor.delete(); mapper.delete(); source.delete(); scalars.delete(); ct.delete(); op.delete(); };
        window.setContainer(container.current);
        window.getRenderer().addVolume(actor); window.getRenderer().resetCamera();
        observer.observe(container.current);
        window.resize(); window.getRenderWindow().render();
        setGeometry(`${shape[2]} × ${shape[1]} × ${shape[0]} display voxels · spacing ${spacing.map(v=>v.toFixed(3)).join(" × ")} µm`);
        setMessage("");
      } catch(e) { if (!abort.signal.aborted) setMessage(`3D preview unavailable: ${String(e)}`); }
    }
    void load();
    return () => { abort.abort(); dispose?.(); };
  }, [image, channel]);
  return <div><div className="volume-controls"><label>Channel<select value={channel} onChange={e=>onChannelChange(Number(e.target.value))}>{image.info.channel_labels.map((name,i)=><option key={i} value={i}>{name}</option>)}</select></label><p className="hint">Drag to rotate · Scroll to zoom<br/>Physical proportions, without Z exaggeration</p></div>
    {message && <p role="status" className="volume-error">{message}</p>}<div className="volume-canvas" ref={container}/>
    <p className="hint viewer-note">{geometry}<br/>Downsampled display preview only. Full-resolution source pixels remain unchanged. This is volume visualization, not super-resolution reconstruction.</p></div>;
}
