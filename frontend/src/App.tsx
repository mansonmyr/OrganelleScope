import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, PointerEvent } from "react";
import { json, request, type ImageRecord } from "./api";
import { SignalChart } from "./components/SignalChart";
import type { LineRoi } from "./types";
import { sampleTrace, buildChannelMetrics } from "./workers/analysisCore";
import { VolumeView } from "./VolumeView";

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
  const [volumeChannel, setVolumeChannel] = useState(0);
  const [axes, setAxes] = useState("");
  const [series, setSeries] = useState(0);
  const [spacing, setSpacing] = useState<Record<string, string>>({ X: "", Y: "", Z: "" });
  const [preview, setPreview] = useState<string>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [roi, setRoi] = useState<LineRoi | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const overlay = useRef<SVGSVGElement>(null);
  const dragging = useRef(false);
  const info = image?.info;
  const available = !!info && !info.needs_axis_confirmation && info.dimensions.T === 1;

  useEffect(() => { json<ImageRecord[]>("/api/images").then(setRecent).catch(e => setError(String(e))); }, []);

  function accept(record: ImageRecord) {
    setImage(record); setZ(0); setAxes(record.info.axes); setSeries(record.info.series_index);
    setSpacing(Object.fromEntries("XYZ".split("").map(a => [a, String(record.info.calibration[a].value_um ?? "")])));
    setRoi(null); setProfile(null); setMode("slice"); setVolumeChannel(0);
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
    if (!image || !roi || !available || dragging.current) return;
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
          const buffer = await (await request(`/api/images/${image.id}/plane?z=${z}&channel=${c}`, { signal: abort.signal })).arrayBuffer();
          const data = image.info.bit_depth === 16 ? new Uint16Array(buffer) : new Uint8Array(buffer);
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
  }, [image, roi, z, available]);

  function point(event: PointerEvent<SVGSVGElement>) {
    const p = overlay.current!.createSVGPoint(); p.x = event.clientX; p.y = event.clientY;
    const c = p.matrixTransform(overlay.current!.getScreenCTM()!.inverse());
    return { x: Math.max(0, Math.min(info!.dimensions.X-1, c.x)), y: Math.max(0, Math.min(info!.dimensions.Y-1, c.y)) };
  }
  return <div className="shell">
    <header><div className="brand"><span className="brand-icon">◎</span><div><h1>OrganelleScope</h1><p>Spatial microscopy workbench</p></div></div>
      <span className="badge">Development build · Import & calibration</span><span className="local"><i /> Local processing</span></header>
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
        <section><p className="eyebrow">PHYSICAL CALIBRATION</p>
          {"XYZ".split("").map(a => <label key={a}>{a} spacing <span className="unit">µm</span><input type="number" min="0.000001" step="any" value={spacing[a]} placeholder="Unknown" onChange={e => setSpacing({...spacing,[a]:e.target.value})}/><small>{info.calibration[a].source}</small>
            {(info.calibration[a].conflict || info.calibration[a].value_um == null) && <small>{Object.entries(info.calibration[a].candidates).map(([s,v])=>`${s}: ${v} µm (not applied)`).join("; ")}</small>}</label>)}
          <button disabled={busy} onClick={confirmImport}>Apply import settings</button><p className="hint">Spacing calibrates coordinates; it does not establish optical resolution.</p>
        </section>
        <section><p className="eyebrow">CHANNELS</p>{info.channel_labels.map((name,i)=><div className="channel" key={i}><i style={{background:colors[i]}}/>{name}</div>)}</section>
        <button className="secondary" onClick={()=>download({...image,selected_z:z,roi,profile},"OrganelleScope-inspection.json")}>Export inspection & profile</button>
      </> : <section className="muted"><p>Original 8/16-bit intensities are preserved.</p><p>Ambiguous axes and missing calibration are shown for review.</p><p>Images stay on this computer.</p></section>}
    </aside><main>
      {error && <div role="alert" className="error">{error}<button onClick={()=>setError("")}>Dismiss</button></div>}
      {info?.warnings.length ? <details className="review" open><summary>Import notes · {info.warnings.length}</summary>{info.warnings.map((w,i)=><p key={i}>{w}</p>)}</details> : null}
      <section className="viewer panel"><div className="viewer-heading"><div><p className="eyebrow">IMAGE EXPLORER</p><h2>{info ? info.filename : "Start with an image"}</h2></div><div className="segmented"><button aria-pressed={mode==="slice"} onClick={()=>setMode("slice")}>XY slice</button><button disabled={!available || !info || info.dimensions.Z<2} aria-pressed={mode==="volume"} onClick={()=>setMode("volume")}>3D preview</button></div></div>
      {!info ? <div className="empty"><div className="empty-symbol">◎</div><h2>A clearer view of cellular space.</h2><p>Open a TIFF to inspect its channels, depth and physical calibration.</p><span>TIFF · OME-TIFF · ImageJ TIFF · up to 4 channels</span></div> : !available ? <div className="empty"><h2>Review the image axes</h2><p>Confirm how dimensions map to channels and depth before viewing.</p></div> : mode==="volume" ? <VolumeView image={image!} channel={volumeChannel} onChannelChange={setVolumeChannel}/> : <>
        <div className="slice-toolbar"><label>Z plane <strong>{z+1} / {info.dimensions.Z}</strong><input aria-label="Z plane" type="range" min={0} max={info.dimensions.Z-1} value={z} onChange={e=>setZ(Number(e.target.value))}/></label><span>{info.calibration.Z.value_um != null ? `${(z*info.calibration.Z.value_um).toFixed(3)} µm from first plane` : "Z spacing unknown"}</span></div>
        <div className="image-stage" style={{aspectRatio:`${info.dimensions.X}/${info.dimensions.Y}`}}>{preview ? <img src={preview} alt={`Composite Z plane ${z+1}`}/> : <p>Loading source plane…</p>}
          <svg ref={overlay} viewBox={`0 0 ${info.dimensions.X} ${info.dimensions.Y}`} onPointerDown={e=>{const p=point(e);dragging.current=true;e.currentTarget.setPointerCapture(e.pointerId);setProfile(null);setRoi({start:p,end:p,sampleSpacingPx:1});}} onPointerMove={e=>{if(dragging.current){const p=point(e);setRoi(r=>r?{...r,end:p}:r);}}} onPointerUp={e=>{if(dragging.current){dragging.current=false;const p=point(e);setRoi(r=>r?{...r,end:p}:r);if(e.currentTarget.hasPointerCapture(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId);}}} onPointerCancel={()=>{dragging.current=false;setRoi(null);}}>
            {roi && <line x1={roi.start.x} y1={roi.start.y} x2={roi.end.x} y2={roi.end.y} stroke="#fff" strokeWidth={Math.max(1,info.dimensions.X/400)} />}
          </svg>
        </div><p className="hint viewer-note">Drag to sample a line on this plane. Display contrast is adjusted per channel; measurements use original values.</p>
      </>}</section>
      {profile && <><SignalChart title="Source intensity profile" subtitle="Native intensity values · approximate 3 px smoothing for peak widths only" distances={profile.distances} xUnit={profile.unit} yLabel="Source gray value" traces={profile.traces}/><div className="widths">{profile.widths.map((w,i)=><span key={i}>{info!.channel_labels[i]} · single-peak FWHM: {w==null?"not available":`${w.toFixed(3)} ${profile.unit}`}</span>)}</div></>}
      <footer><span>Foundation milestone · Quantitative reconstruction and molecular agent are in development.</span><span>Source → calibration → measurement</span></footer>
    </main></div></div>;
}
