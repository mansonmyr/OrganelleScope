import { useEffect, useState } from "react";
import type { ChangeEvent } from "react";
import { json, request, type ImageRecord } from "./api";
import { SignalChart } from "./components/SignalChart";
import type { LineRoi } from "./types";
import { sampleTrace, buildChannelMetrics } from "./workers/analysisCore";
import { CalibrationHelp } from "./CalibrationHelp";
import { ProcessingPanel, rawProcessing, isProcessed, type ProcessingConfig } from "./ProcessingPanel";
import { VolumeView } from "./VolumeView";

import { RoiOverlay, type AreaROI, type DrawTool } from "./RoiOverlay";
import { StatisticsPanel, type AnalysisResult } from "./StatisticsPanel";

const colors = ["#ff4969", "#31d6a0", "#629aff", "#dddddf"];
type Profile = { distances: number[]; unit: string; traces: { label: string; color: string; values: number[] }[]; widths: (number | null)[] };

function download(value: unknown, name: string) {
  const href = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
  const link = document.createElement("a"); link.href = href; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(href), 1000);
}

export default function App() {
  const [image, setImage] = useState<ImageRecord | null>(null);
  const [recent, setRecent] = useState<ImageRecord[]>([]);
  const [z, setZ] = useState(0);
  const [mode, setMode] = useState<"slice" | "volume">("slice");
  const [volumeChannel, setVolumeChannel] = useState(-1);
  const [axes, setAxes] = useState("");
  const [series, setSeries] = useState(0);
  const [spacing, setSpacing] = useState<Record<string, string>>({ X: "", Y: "", Z: "" });
  const [preview, setPreview] = useState<string>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [roi, setRoi] = useState<LineRoi | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loadingSaved, setLoadingSaved] = useState(false);
  const [drawingActions, setDrawingActions] = useState<HTMLDivElement | null>(null);
  const [tool, setTool] = useState<DrawTool>("line");
  const [areas, setAreas] = useState<AreaROI[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [thresholdMode, setThresholdMode] = useState<'zero'|'manual'|'costes'>('costes');
  const [thresholds, setThresholds] = useState<number[]>([0,0,0,0]);
  const [target, setTarget] = useState(0);
  const [processing,setProcessing]=useState<ProcessingConfig>({...rawProcessing});
  const [measurementSource,setMeasurementSource]=useState<"raw"|"processed">("raw");
  const selectedProcessing=measurementSource==="processed"?processing:rawProcessing;
  const info = image?.info;
  const available = !!info && !info.needs_axis_confirmation && info.dimensions.T === 1;

  useEffect(() => { json<ImageRecord[]>("/api/images").then(setRecent).catch(e => setError(String(e))); }, []);

  function accept(record: ImageRecord) {
    setImage(record); setProcessing({...rawProcessing});setMeasurementSource("raw"); setZ(0); setAxes(record.info.axes); setSeries(record.info.series_index);
    setSpacing(Object.fromEntries("XYZ".split("").map(a => [a, String(record.info.calibration[a].value_um ?? "")])));
    setRoi(null); setAreas([]); setAnalysis(null); setTarget(0); setProfile(null); setMode("slice"); setVolumeChannel(-1);
    setRecent(records => [record, ...records.filter(r => r.id !== record.id)].slice(0,20));
  }
  async function importImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; if (!file) return;
    setBusy(true); setError("");
    try { const form = new FormData(); form.append("file", file); accept(await json<ImageRecord>("/api/images", { method: "POST", body: form })); }
    catch (e) { setError(String(e)); } finally { setBusy(false); event.target.value = ""; }
  }
  async function confirmImport() {
    if (!image) return;
    setBusy(true); setError("");
    try {
      const overrides = Object.fromEntries(Object.entries(spacing).filter(([a, v]) => v !== "" &&
        (Number(v) !== image.info.calibration[a].value_um || image.info.calibration[a].conflict)).map(([a,v]) => [a, Number(v)]));
      // Preserve previous user overrides when a later correction changes another field.
      const previous = (image.options as { spacing_um?: Record<string, number> }).spacing_um ?? {};
      accept(await json<ImageRecord>(`/api/images/${image.id}/inspect`, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ series_index: series, axes: series === image.info.series_index ? axes : null,
          spacing_um: series === image.info.series_index ? { ...previous, ...overrides } : {} }) }));
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }

  useEffect(() => {
    setPreview(undefined); setProfile(null);
    if (!image || !available) return;
    const abort = new AbortController(); let href: string | undefined;
    request(`/api/images/${image.id}/preview?z=${z}`, { signal: abort.signal })
      .then(r => r.blob()).then(blob => { if (!abort.signal.aborted) { href = URL.createObjectURL(blob); setPreview(href); } })
      .catch(e => { if (!abort.signal.aborted) setError(String(e)); });
    return () => { abort.abort(); if (href) URL.revokeObjectURL(href); };
  }, [image, z, available]);

  useEffect(() => {
    setProfile(null);
    if (!image || !roi || !available) return;
    const selected = roi;
    const abort = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const { X: width, Y: height, C: count } = image.info.dimensions;
        const sx = image.info.calibration.X.value_um, sy = image.info.calibration.Y.value_um;
        const length = Math.hypot(selected.end.x - selected.start.x, selected.end.y - selected.start.y);
        if (!length) return;
        const physical = sx != null && sy != null;
        const factor = physical ? Math.hypot((selected.end.x-selected.start.x)*sx!, (selected.end.y-selected.start.y)*sy!) / length : 1;
        const traces = await Promise.all(Array.from({ length: count }, async (_, c) => {
          const processed=isProcessed(selectedProcessing);
          const buffer = await (await request(`/api/images/${image.id}/${processed?'processing/plane':'plane'}?z=${z}&channel=${c}`, { signal: abort.signal,...(processed?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(selectedProcessing)}:{}) })).arrayBuffer();
          const data = processed?new Float32Array(buffer):image.info.bit_depth === 16 ? new Uint16Array(buffer) : new Uint8Array(buffer);
          return sampleTrace(data, width, height, selected, image.info.channel_labels[c], colors[c]);
        }));
        if (abort.signal.aborted) return;
        const distances = traces[0].distancesPx.map(d => d * factor);
        const metrics = traces.map(t => buildChannelMetrics(t, t.distancesPx, distances, "um"));
        setProfile({ distances, unit: physical ? "µm" : "px", traces: traces.map(t => ({ label: t.label, color: t.color, values: t.rawValues })),
          widths: metrics.map(m => m.peaks.length === 1 ? m.peaks[0].fwhmPhysical : null) });
      } catch (e) { if (!abort.signal.aborted) setError(String(e)); }
    }, 180);
    return () => { abort.abort(); clearTimeout(timer); };
  }, [image, roi, z, available, processing, measurementSource]);

  useEffect(() => {
    if (!image) return;
    const abort = new AbortController();
    setLoadingSaved(true);
    json<AnalysisResult>(`/api/images/${image.id}/analysis`, {signal:abort.signal}).then(saved=>{
      if(abort.signal.aborted)return;
      if(saved.request.processing){setProcessing(saved.request.processing);setMeasurementSource(isProcessed(saved.request.processing)?"processed":"raw");}
      setAreas(saved.request.rois);setTarget(saved.request.target_channel);setThresholdMode(saved.request.threshold_mode);
      setThresholds(saved.request.thresholds.length?saved.request.thresholds:[0,0,0,0]);setAnalysis(saved);
    }).catch(()=>{/* No saved analysis for a new import or revised settings. */}).finally(()=>{if(!abort.signal.aborted)setLoadingSaved(false);});
    return ()=>abort.abort();
  }, [image]);
  async function exportInspection() {
    if(!image)return;setBusy(true);setError("");
    try {
      const recipe=await json(`/api/images/${image.id}/processing/recipe`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(processing)});
      download({...image,selected_z:z,roi,profile,profile_source:measurementSource,processing_recipe:recipe,measurement_source:measurementSource,area_rois:areas,analysis},"OrganelleScope-inspection.json");
    } catch(e){setError(String(e));}finally{setBusy(false);}
  }
  async function calculate() {
    if(!image)return;setBusy(true);setError("");setAnalysis(null);
    try { setAnalysis(await json<AnalysisResult>(`/api/images/${image.id}/analysis`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({processing:selectedProcessing,rois:areas,target_channel:target,threshold_mode:thresholdMode,thresholds:thresholds.slice(0,image.info.dimensions.C)})})); }
    catch(e){setError(String(e));}finally{setBusy(false);}
  }
  return <div className="shell">
    <header><div className="brand"><img className="brand-icon" src="./branding/icon.png" alt="OrganelleScope microscope and cell logo"/><div><h1>OrganelleScope</h1><p>Spatial microscopy workbench</p></div></div>
      <span className="badge">Development build · ROI statistics</span><span className="local"><i /> Local processing</span></header>
    <div className="workspace"><aside>
      <p className="eyebrow">WORKSPACE / 01</p><h2>Your image, in context.</h2><p className="muted">Inspect the source. Confirm the scale. Explore the volume.</p>
      <label className={`import-button ${busy ? "disabled" : ""}`}><input type="file" accept=".tif,.tiff" disabled={busy} onChange={importImage} />{busy ? "Working…" : "+ Open TIFF / OME-TIFF"}</label>
      {recent.length > 0 && <label>Recent imports<select aria-label="Recent imports" value={image?.id ?? ""} disabled={busy} onChange={e => { const record = recent.find(r=>r.id===e.target.value); if (record) accept(record); }}><option value="" disabled>Select a saved import</option>{recent.map(r=><option value={r.id} key={r.id}>{r.info.filename} · {r.id.slice(0,6)}</option>)}</select></label>}
      {info ? <>
        <section><p className="eyebrow">SOURCE IMAGE</p><h3>{info.filename}</h3>
          <dl><dt>Storage</dt><dd>{info.bit_depth}-bit · {info.dtype}</dd><dt>Dimensions</dt><dd>{info.shape.join(" × ")}</dd><dt>Axes in file</dt><dd>{info.source_axes}</dd><dt>Decoded size</dt><dd>{(info.decoded_bytes/1024**2).toFixed(1)} MiB</dd></dl>
          <label>Image series<select value={series} onChange={e => setSeries(Number(e.target.value))}>{Array.from({length:info.series_count},(_,i)=><option key={i} value={i}>Series {i+1}</option>)}</select></label>
          <label>Confirmed axis order<input value={axes} onChange={e => setAxes(e.target.value.toUpperCase())} maxLength={6} /></label>
          <p className="hint">C = channels · Z = depth · Y/X = image · T = time</p>
        </section>
        <section><p className="eyebrow">PHYSICAL CALIBRATION</p><CalibrationHelp/>
          {"XYZ".split("").map(a => <label key={a}>{a} spacing <span className="unit">µm</span><input type="number" min="0.000001" step="any" value={spacing[a]} placeholder="Unknown" onChange={e => setSpacing({...spacing,[a]:e.target.value})}/><small>{info.calibration[a].source}</small>
            {(info.calibration[a].conflict || info.calibration[a].value_um == null) && <small>{Object.entries(info.calibration[a].candidates).map(([s,v])=>`${s}: ${v} µm (not applied)`).join("; ")}</small>}</label>)}
          <button disabled={busy} onClick={confirmImport}>Apply import settings</button><p className="hint">Spacing calibrates coordinates; it does not establish optical resolution.</p>
        </section>
        <section><p className="eyebrow">CHANNELS</p>{info.channel_labels.map((name,i)=><div className="channel" key={i}><i style={{background:colors[i]}}/>{name}</div>)}</section>
        <button className="secondary" disabled={busy||loadingSaved} onClick={exportInspection}>Export measurements & ROIs</button>
      </> : <section className="muted"><p>Original 8/16-bit intensities are preserved.</p><p>Ambiguous axes and missing calibration are shown for review.</p><p>Images stay on this computer.</p></section>}
    </aside><main>
      {error && <div role="alert" className="error">{error}<button onClick={()=>setError("")}>Dismiss</button></div>}
      {info?.warnings.length ? <details className="review" open><summary>Import notes · {info.warnings.length}</summary>{info.warnings.map((w,i)=><p key={i}>{w}</p>)}</details> : null}
      <section className="viewer panel"><div className="viewer-heading"><div><p className="eyebrow">IMAGE EXPLORER</p><h2>{info ? info.filename : "Start with an image"}</h2></div><div className="segmented"><button aria-pressed={mode==="slice"} onClick={()=>setMode("slice")}>XY slice</button><button disabled={!available || !info || info.dimensions.Z<2} aria-pressed={mode==="volume"} onClick={()=>setMode("volume")}>3D preview</button></div></div>
      {!info ? <div className="empty"><img className="empty-logo" src="./branding/brand-logo.jpg" alt="OrganelleScope — Cellular Exploration & Analysis"/><h2>A clearer view of cellular space.</h2><p>Open a TIFF to inspect its channels, depth and physical calibration.</p><span>TIFF · OME-TIFF · ImageJ TIFF · up to 4 channels</span></div> : !available ? <div className="empty"><h2>Review the image axes</h2><p>Confirm how dimensions map to channels and depth before viewing.</p></div> : mode==="volume" ? <VolumeView image={image!} channel={volumeChannel} onChannelChange={setVolumeChannel}/> : <>
        <div className="slice-toolbar"><label>Z plane <strong>{z+1} / {info.dimensions.Z}</strong><input aria-label="Z plane" type="range" min={0} max={info.dimensions.Z-1} value={z} onChange={e=>{setZ(Number(e.target.value));setRoi(null);}}/></label><span>{info.calibration.Z.value_um != null ? `${(z*info.calibration.Z.value_um).toFixed(3)} µm from first plane` : "Z spacing unknown"}</span></div>

        <div className="image-stage" style={{aspectRatio:`${info.dimensions.X}/${info.dimensions.Y}`}}>{preview ? <img src={preview} alt={`Composite Z plane ${z+1}`}/> : <p>Loading source plane…</p>}
          <RoiOverlay controlsContainer={drawingActions} disabled={busy || loadingSaved} key={`${image!.id}-${z}-${tool}`} width={info.dimensions.X} height={info.dimensions.Y} z={z} tool={tool} rois={areas} line={roi} onLine={setRoi} onAdd={r=>{if(busy)return;setAreas(a=>[...a,r]);setAnalysis(null);}}/>

        </div>
        <div className="drawing-dock" role="toolbar" aria-label="Image drawing tools"><div className="roi-tools"><label>Drawing tool<select aria-label="Drawing tool" disabled={busy} value={tool} onChange={e=>setTool(e.target.value as DrawTool)}><option value="line">Line profiler</option><option value="circle">Circular ROI</option><option value="polygon">Polygonal ROI</option></select></label><span>{tool==='polygon'?'Click vertices, then finish the polygon.':tool==='circle'?'Drag from the center to the circle edge.':'Drag to sample a line.'}</span></div><div ref={setDrawingActions}/></div>
        <p className="hint viewer-note">ROIs belong to their selected Z plane. Display contrast is adjusted per channel; select raw or processed intensities in ROI measurements below.</p>
      </>}</section>
      {image && available && <ProcessingPanel key={image.id} imageId={image.id} z={z} labels={info!.channel_labels} bitDepth={info!.bit_depth} value={processing} disabled={busy||loadingSaved} onChange={config=>{setProcessing(config);setAnalysis(null);if(!isProcessed(config))setMeasurementSource("raw");}}/>}
      {image && available && <section className="panel statistics"><p className="eyebrow">AREA ANALYSIS</p><h2>ROI measurements</h2><p className="hint">Draw circular or polygonal ROIs above. Each region is measured separately on its own plane.</p>
        <label>Measurement source<select aria-label="Measurement source" disabled={busy||loadingSaved} value={measurementSource} onChange={e=>{const source=e.target.value as 'raw'|'processed';setMeasurementSource(source);setAnalysis(null);if(source==='processed'&&thresholdMode==='costes')setThresholdMode('manual');}}><option value="raw">Raw source intensities</option><option value="processed" disabled={!isProcessed(processing)}>Processed intensities (applied recipe)</option></select></label><p className="hint">This selection applies to line profiles and ROI statistics. Raw images remain visible in the image explorer and 3D preview.</p>
        <div className="roi-list">{areas.map((r,i)=><div key={r.id}>ROI {i+1} · {r.kind} · Z {r.z+1} <button disabled={busy} onClick={()=>{setAreas(a=>a.filter(x=>x.id!==r.id));setAnalysis(null);}}>Delete ROI {i+1}</button></div>)}</div>
        <div className="roi-tools"><label>Threshold method<select disabled={busy} value={thresholdMode} onChange={e=>{setThresholdMode(e.target.value as typeof thresholdMode);setAnalysis(null);}}><option value="costes" disabled={measurementSource==='processed'}>Costes-style automatic (raw only)</option><option value="manual">Manual per channel</option><option value="zero">Zero threshold</option></select></label><label>Regression target<select disabled={busy} value={target} onChange={e=>{setTarget(Number(e.target.value));setAnalysis(null);}}>{info!.channel_labels.map((l,i)=><option key={i} value={i}>{l}</option>)}</select></label></div>
        {thresholdMode==='manual' && info!.channel_labels.map((l,i)=><label key={i}>{l} threshold<input disabled={busy} type="number" min="0" max={2**info!.bit_depth-1} value={thresholds[i]??0} onChange={e=>{setThresholds(t=>Array.from({length:info!.dimensions.C},(_,j)=>j===i?Number(e.target.value):t[j]??0));setAnalysis(null);}}/></label>)}
        <button disabled={busy || loadingSaved || !areas.length || info!.dimensions.C<2} onClick={calculate}>{busy?'Calculating…':'Calculate ROI statistics'}</button><p className="hint">At least two channels are needed. Results and ROI coordinates are saved locally after calculation and included in the export.</p>
      </section>}
      {analysis && <StatisticsPanel analysis={analysis}/>}
      {profile && <><SignalChart title={`${measurementSource==='processed'?'Processed':'Source'} intensity profile`} subtitle="Selected measurement intensities · approximate 3 px smoothing for peak widths only" distances={profile.distances} xUnit={profile.unit} yLabel={measurementSource==='processed'?"Processed gray value":"Source gray value"} traces={profile.traces}/><div className="widths">{profile.widths.map((w,i)=><span key={i}>{info!.channel_labels[i]} · single-peak FWHM: {w==null?"not available":`${w.toFixed(3)} ${profile.unit}`}</span>)}</div></>}
      <footer><span>Foundation milestone · Quantitative reconstruction and molecular agent are in development.</span><span>Source → calibration → measurement</span></footer>
    </main></div></div>;
}
