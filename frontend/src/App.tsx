import {LUTS,channelLuts,lutCss} from './channelLuts';
import {ChannelPanel} from './ChannelPanel';
import {PreviewZoom} from './PreviewZoom';
import {RoiSummaryPanel} from './RoiSummaryPanel';
import {hasRetiredProcessing,rawProcessingCopy} from './retiredProcessing';
import { useEffect, useState, useRef } from "react";
import type { ChangeEvent } from "react";
import { json, request, type ImageRecord } from "./api";
import { SignalChart } from "./components/SignalChart";
import type { LineRoi } from "./types";
import { sampleTrace, buildChannelMetrics } from "./workers/analysisCore";
import { CalibrationHelp } from "./CalibrationHelp";
import {SegmentationPanel} from './SegmentationPanel';
import { ProcessingPanel, rawProcessing, isProcessed, type ProcessingConfig } from "./ProcessingPanel";
import { ValidationPanel } from "./ValidationPanel";
import { OrthogonalWorkspace } from "./OrthogonalWorkspace";
import { EvidencePanel } from "./EvidencePanel";
import {ProjectStateProvider,type WorkspaceData} from './ProjectContext';
import {AssistantSetupBanner} from './AssistantSetupBanner';
import {AssistantPanel} from './AssistantPanel';
import {sliceSnapshot,downloadSnapshot,type VolumeCapture} from './previewSnapshot';
import { VolumeView } from "./VolumeView";

import { RoiOverlay, type AreaROI, type DrawTool } from "./RoiOverlay";
import {ExperimentPanel} from './ExperimentPanel';
import {BatchPanel} from './BatchPanel';
import {CircleSizeEditor} from "./CircleSizeEditor";
import { StatisticsPanel, type AnalysisResult } from "./StatisticsPanel";

type ProjectRecord={id:string;name:string;revision:number;image:ImageRecord|null;state:{core:Record<string,any>;workspaces:WorkspaceData}};
type ProjectSummary={id:string;name:string;revision:number;updated_utc:string};
const colors = ["#ff4969", "#31d6a0", "#629aff", "#dddddf"];
type Profile = { distances: number[]; unit: string; traces: { label: string; color: string; values: number[] }[]; widths: (number | null)[] };

function download(value: unknown, name: string) {
  const href = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
  const link = document.createElement("a"); link.href = href; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(href), 1000);
}

export default function App() {
  const [projectData,setProjectData]=useState<WorkspaceData>({});
  const [project,setProject]=useState<ProjectRecord|null>(null),[projects,setProjects]=useState<ProjectSummary[]>([]),[projectName,setProjectName]=useState('Untitled project'),[projectBusy,setProjectBusy]=useState(false),[generation,setGeneration]=useState(0),[projectMessage,setProjectMessage]=useState('');
  const [recovery,setRecovery]=useState<ProjectRecord|null>(null),[recoveryMessage,setRecoveryMessage]=useState('');
  const skipSaved=useRef<string>();
  const [image, setImage] = useState<ImageRecord | null>(null);
  const [recent, setRecent] = useState<ImageRecord[]>([]);
  const [z, setZ] = useState(0);
  const [workspace,setWorkspace]=useState<"images"|"processing"|"roi"|"associations"|"volume"|"validation"|"evidence"|"assistant"|"batch">("images");
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
  const snapshotStage=useRef<HTMLDivElement>(null),volumeCapture=useRef<(()=>Promise<VolumeCapture>)|null>(null);
  const [snapshotBusy,setSnapshotBusy]=useState(false),[snapshotMessage,setSnapshotMessage]=useState(''),[snapshotDetails,setSnapshotDetails]=useState<Record<string,unknown>>(),[includeSnapshotRois,setIncludeSnapshotRois]=useState(true);
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
  const displayLuts=channelLuts(projectData['Display.luts'],info?.dimensions.C??0),lutQuery=displayLuts.join(',');
  function changeLut(index:number,name:string){const next=[...displayLuts];next[index]=name as typeof next[number];setProjectData(data=>({...data,'Display.luts':next}));}
  const contrast=projectData['Display.contrast']==='auto'?'auto':'native';
  const available = !!info && !info.needs_axis_confirmation && info.dimensions.T === 1;

  useEffect(() => { json<ImageRecord[]>("/api/images").then(setRecent).catch(e => setError(String(e))); }, []);

  function accept(record: ImageRecord, restoring=false) {
    skipSaved.current=restoring?record.id:undefined;
    setProject(null);setProjectName(record.info.filename.replace(/\.ome\.tiff?$|\.tiff?$/i,''));setProjectData({});setGeneration(g=>g+1);setProjectMessage('Image open. Saving a project is optional; save to retain this workspace.');
    setSnapshotDetails(undefined);setSnapshotMessage('');setWorkspace("images");setImage(record); setProcessing({...rawProcessing});setMeasurementSource("raw"); setZ(0); setAxes(record.info.axes); setSeries(record.info.series_index);
    setSpacing(Object.fromEntries("XYZ".split("").map(a => [a, String(record.info.calibration[a].value_um ?? "")])));
    setRoi(null); setAreas([]); setAnalysis(null); setTarget(0); setProfile(null); setMode("slice"); setVolumeChannel(-1);
    setRecent(records => [record, ...records.filter(r => r.id !== record.id)].slice(0,20));
  }
  async function importImage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; if (!file) return;
    if((image||Object.keys(projectData).length>0)&&!window.confirm('Opening another image starts a new project. Save first if you want to keep current changes. Continue?')){event.target.value='';return;}
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
    setPreview(undefined);
    if (!image || !available) return;
    const abort = new AbortController(); let href: string | undefined;
    request(`/api/images/${image.id}/preview?z=${z}&luts=${lutQuery}${contrast==='auto'?'&contrast=auto':''}`, { signal: abort.signal })
      .then(r => r.blob()).then(blob => { if (!abort.signal.aborted) { href = URL.createObjectURL(blob); setPreview(href); } })
      .catch(e => { if (!abort.signal.aborted) setError(String(e)); });
    return () => { abort.abort(); if (href) URL.revokeObjectURL(href); };
  }, [image, z, available, lutQuery, contrast]);

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
    if (!image || skipSaved.current===image.id) return;
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

  useEffect(()=>{json<ProjectSummary[]>('/api/projects').then(setProjects).catch(e=>setError(String(e)));},[]);
  useEffect(()=>{json<ProjectRecord|null>('/api/recovery').then(v=>{if(v?.state?.core)setRecovery(v);}).catch(e=>setRecoveryMessage(String(e)));},[]);
  const recoveryBody=JSON.stringify({name:projectName,image_id:image?.id??null,expected_image_info:image?.info??null,state:{core:{layout_version:2,z,workspace,mode,volumeChannel,roi,areas,analysis,thresholdMode,thresholds,target,processing,measurementSource,tool},workspaces:projectData}});
  useEffect(()=>{if(!image||loadingSaved||projectBusy)return;const abort=new AbortController();const timer=setTimeout(()=>{json('/api/recovery',{signal:abort.signal,method:'POST',headers:{'Content-Type':'application/json'},body:recoveryBody}).then(()=>{if(!abort.signal.aborted)setRecoveryMessage('Recovery copy saved locally.');}).catch(e=>{if(!abort.signal.aborted)setRecoveryMessage('Recovery copy not saved: '+String(e));});},3000);return()=>{clearTimeout(timer);abort.abort();};},[recoveryBody,loadingSaved,projectBusy,image?.id]);
  function snapshot(){return {core:{layout_version:2,z,workspace,mode,volumeChannel,roi,areas,analysis,thresholdMode,thresholds,target,processing,measurementSource,tool},workspaces:projectData};}
  async function saveProject(asNew=false){
    setProjectBusy(true);setError('');
    try{const saved=await json<ProjectRecord>(`/api/projects${project&&!asNew?'/'+project.id:''}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:projectName,image_id:image?.id??null,expected_image_info:image?.info??null,state:snapshot(),expected_revision:project&&!asNew?project.revision:null})});setProject(saved);setProjectMessage(`Saved revision ${saved.revision} on this computer.`);setProjects(await json<ProjectSummary[]>('/api/projects'));return saved;}
    catch(e){setError(String(e));}finally{setProjectBusy(false);}
  }
  function restoreWorkspace(saved:ProjectRecord){const retired=hasRetiredProcessing(saved.state);const state=retired?rawProcessingCopy(saved.state):saved.state;const c=state.core??{};
      if(saved.image){accept(saved.image,true);}else{setImage(null);}
      setProject(retired||saved.id==='recovery'?null:saved);setProjectName(saved.name+(retired?' (recalculation copy)':''));setProjectData(state.workspaces??{});setGeneration(g=>g+1);
      setZ(c.z??0);setWorkspace(c.layout_version!==2&&c.workspace==='images'&&c.mode==='volume'?'volume':c.workspace??'images');setMode(c.mode??'slice');setVolumeChannel(c.volumeChannel??-1);setRoi(c.roi??null);setAreas(c.areas??[]);setAnalysis(c.analysis??null);setThresholdMode(c.thresholdMode??'costes');setThresholds(c.thresholds??[0,0,0,0]);setTarget(c.target??0);setProcessing(c.processing??{...rawProcessing});setMeasurementSource(c.measurementSource??'raw');setTool(c.tool??'line');setLoadingSaved(false);setProjectMessage(retired?'Denoising/deconvolution removed: opened a recalculation copy with the original image, calibration and ROIs. Previous reports remain in the original project. Review thresholds and the retained background/smoothing recipe before recalculating.':`Opened revision ${saved.revision}; ${saved.image?'source SHA-256 verified.':'evidence-only project.'}`);
  }
  async function recoverWorkspace(){if((image||Object.keys(projectData).length)&&!window.confirm('Restore the recovery copy? Current unsaved changes will be replaced.'))return;setProjectBusy(true);try{const saved=await json<ProjectRecord>('/api/recovery');if(saved?.state)restoreWorkspace(saved);else setRecoveryMessage('No recovery copy exists.');}catch(e){setError(String(e));}finally{setProjectBusy(false);}}
  async function exportArchive(){if(!project)return;setProjectBusy(true);try{const response=await request(`/api/projects/${project.id}/archive`);const href=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=href;a.download='OrganelleScope-project.zip';a.click();setTimeout(()=>URL.revokeObjectURL(href),1000);}catch(e){setError(String(e));}finally{setProjectBusy(false);}}
  async function importArchive(file?:File){if(!file)return;if(image&&!window.confirm('Open the portable project? Save current changes first.'))return;setProjectBusy(true);try{const form=new FormData();form.append('file',file);const saved=await json<ProjectRecord>('/api/project-archives/import',{method:'POST',body:form});restoreWorkspace(saved);setProjects(await json<ProjectSummary[]>('/api/projects'));}catch(e){setError(String(e));}finally{setProjectBusy(false);}}
  async function openProject(id:string){
    if(!id)return;
    if((image||Object.keys(projectData).length)&&!window.confirm('Open the saved project? Any changes since your last save will be discarded.'))return;
    setProjectBusy(true);setError('');
    try{const saved=await json<ProjectRecord>('/api/projects/'+id);restoreWorkspace(saved);
    }catch(e){setError(String(e));}finally{setProjectBusy(false);}
  }
  async function exportInspection() {
    if(!image)return;setBusy(true);setError("");
    try {
      const recipe=await json(`/api/images/${image.id}/processing/recipe`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(processing)});
      download({...image,selected_z:z,display_luts:displayLuts,roi,profile,profile_source:measurementSource,processing_recipe:recipe,measurement_source:measurementSource,area_rois:areas,analysis},"OrganelleScope-inspection.json");
    } catch(e){setError(String(e));}finally{setBusy(false);}
  }
  async function capturePreview(){
    if(!image||!available)return;
    setSnapshotBusy(true);setSnapshotMessage('');
    const capturedImage=image,capturedMode=mode,capturedZ=z;
    try{
      const capture=capturedMode==='volume'?await (volumeCapture.current?volumeCapture.current():Promise.reject(new Error('Wait for the 3D preview to finish loading.'))):{dataUrl:await sliceSnapshot(snapshotStage.current!,includeSnapshotRois),details:{z_index:capturedZ,channel_luts:displayLuts,xy_display_zoom_percent:projectData['PreviewZoom.zoom']??100,capture_extent:'Whole XY plane; inspection zoom does not crop the exported PNG',includes_overlays:includeSnapshotRois,contrast,display_range:contrast==='native'?[0,2**capturedImage.info.bit_depth-1]:null,display_note:'Display PNG, not native TIFF intensities',rois:includeSnapshotRois?areas.filter(r=>r.z===capturedZ):[],line:includeSnapshotRois?roi:null}};
      const details={schema:'organelle-preview-snapshot-1',created_utc:new Date().toISOString(),source_sha256:capturedImage.sha256,image_id:capturedImage.id,image_info:capturedImage.info,preview_mode:capturedMode,measurement_source:'raw',display_only:true,scope:'Display snapshot, not native quantitative image data. XY contrast is per-channel; 3D is downsampled. See recorded display settings.',...capture.details};
      downloadSnapshot(capture.dataUrl,`OrganelleScope-${capturedImage.info.filename.replace(/\.tiff?$/i,'')}-${capturedMode==='slice'?`Z${capturedZ+1}`:'3D'}-${Date.now()}.png`);
      setSnapshotDetails(details);setSnapshotMessage('PNG captured. Export snapshot details to retain calibration, source identity and display settings.');
    }catch(e){setSnapshotMessage(String(e));}finally{setSnapshotBusy(false);}
  }
  async function calculate() {
    if(!image)return;setBusy(true);setError("");setAnalysis(null);
    try { setAnalysis(await json<AnalysisResult>(`/api/images/${image.id}/analysis`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({processing:selectedProcessing,rois:areas,target_channel:target,threshold_mode:thresholdMode,thresholds:thresholds.slice(0,image.info.dimensions.C)})})); }
    catch(e){setError(String(e));}finally{setBusy(false);}
  }
  return <div className="shell"><AssistantSetupBanner/>
    <header><div className="brand"><img className="brand-icon" src="./branding/icon.png" alt="OrganelleScope microscope and cell logo"/><div><h1>OrganelleScope</h1><p>Spatial microscopy workbench</p></div></div>
      <span className="badge">Research workbench · 1.0</span><span className="local"><i /> Local processing</span></header>
    <div className="workspace"><aside aria-label="Workspace">
      <p className="eyebrow">WORKSPACE / 01</p><h2>Your image, in context.</h2><p className="muted">Inspect the source. Confirm the scale. Explore the volume.</p>
      <label className={`import-button ${busy ? "disabled" : ""}`}><input type="file" accept=".tif,.tiff" disabled={busy||projectBusy} onChange={importImage} />{busy ? "Working…" : "+ Open TIFF / OME-TIFF"}</label>
      {recent.length > 0 && <label>Recent imports<select aria-label="Recent imports" value={image?.id ?? ""} disabled={busy||projectBusy} onChange={e => { const record = recent.find(r=>r.id===e.target.value); if (record&&(!image&&!Object.keys(projectData).length||window.confirm('Open this import as a new project? Save current changes first.'))) accept(record); }}><option value="" disabled>Select a saved import</option>{recent.map(r=><option value={r.id} key={r.id}>{r.info.filename} · {r.id.slice(0,6)}</option>)}</select></label>}
      <section className="workspace-projects" aria-label="Projects and recovery"><h3>Projects & recovery</h3>
    <div className="project-bar"><button disabled={!project||projectBusy} onClick={exportArchive}>Export saved project archive</button><label>Import portable project<input disabled={projectBusy} type="file" accept=".zip" onChange={e=>{void importArchive(e.target.files?.[0]);e.target.value='';}}/></label>{recovery&&<button disabled={projectBusy} onClick={recoverWorkspace}>Restore recovery copy</button>}<span className="hint">{recoveryMessage}</span></div>
    <div className="project-bar" aria-label="Project controls"><label>Project name<input aria-label="Project name" value={projectName} maxLength={120} onChange={e=>setProjectName(e.target.value)}/></label><button disabled={projectBusy||busy||loadingSaved||!projectName.trim()} onClick={()=>saveProject()}>{projectBusy?'Working…':'Save project'}</button><button className="secondary" disabled={projectBusy||busy||loadingSaved} onClick={()=>saveProject(true)}>Save as new</button><label>Open saved project<select aria-label="Open saved project" disabled={projectBusy||busy} value={project?.id??''} onChange={e=>openProject(e.target.value)}><option value="">Select project</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name} · r{p.revision}</option>)}</select></label><span className="hint" role="status">{project&&JSON.stringify(snapshot())!==JSON.stringify(project.state)?'Unsaved changes · assistant uses the current workspace.':projectMessage||'Projects keep the imported image and analysis on this computer. Save before switching images.'}</span></div>
      </section>
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
        <ChannelPanel onQuality={quality=>setProjectData(data=>({...data,'ChannelPanel.quality':quality}))} image={image!} z={z} disabled={busy||loadingSaved||projectBusy} onUpdate={updated=>{setImage(updated);setRecent(rows=>rows.map(row=>row.id===updated.id?updated:row));setAnalysis(null);setProfile(null);setSnapshotDetails(undefined);setProjectData(data=>Object.fromEntries(Object.entries(data).filter(([key])=>!['Segmentation.report','Segmentation.mesh','OrthogonalWorkspace.report','ValidationPanel.spatial','ValidationPanel.sensitivity','ChannelPanel.quality'].includes(key))));setProjectMessage('Channel names updated locally. ROIs are retained; recalculate reports with the new labels. Saved revisions remain unchanged.');}}/>
        <section><p className="eyebrow">DISPLAY COLOURS</p>{info.channel_labels.map((name,i)=><div className="channel channel-lut" key={i}><i style={{background:lutCss(displayLuts[i])}}/><label>{name}<select aria-label={`${name} display LUT`} value={displayLuts[i]} onChange={e=>changeLut(i,e.target.value)}>{Object.entries(LUTS).map(([key,lut])=><option value={key} key={key}>{lut.label}</option>)}</select></label></div>)}<p className="hint">LUTs change preview colours only. Measurements use source intensities.</p><button className="secondary" onClick={()=>setProjectData(data=>({...data,'Display.luts':undefined}))}>Reset channel LUTs</button></section>
        <button className="secondary" disabled={busy||loadingSaved} onClick={exportInspection}>Export measurements & ROIs</button>
      </> : <section className="muted"><p>Original 8/16-bit intensities are preserved.</p><p>Ambiguous axes and missing calibration are shown for review.</p><p>Images stay on this computer.</p></section>}
    </aside><main>
      {error && <div role="alert" className="error">{error}<button onClick={()=>setError("")}>Dismiss</button></div>}
      {info?.warnings.length ? <details className="review" open><summary>Import notes · {info.warnings.length}</summary>{info.warnings.map((w,i)=><p key={i}>{w}</p>)}</details> : null}
      <ProjectStateProvider key={generation} data={projectData} setData={setProjectData}>
      <section className="viewer panel" aria-label="Image preview"><div className="viewer-heading"><div><p className="eyebrow">IMAGE EXPLORER</p><h2>{info ? info.filename : "Start with an image"}</h2></div><div className="segmented"><button aria-pressed={mode==="slice"} onClick={()=>setMode("slice")}>XY slice</button><button disabled={!available || !info || info.dimensions.Z<2} aria-pressed={mode==="volume"} onClick={()=>setMode("volume")}>3D preview</button></div></div>
      {info&&<div className="contrast-toolbar"><label>Preview contrast<select aria-label="Preview contrast" value={contrast} onChange={e=>setProjectData(data=>({...data,'Display.contrast':e.target.value}))}><option value="native">Native range · no automatic enhancement</option><option value="auto">Automatic contrast · display only</option></select></label><span className="hint">Native range maps zero to black and the storage maximum to full colour. Acquisition display settings may differ. Quantitative pixels are unchanged.</span></div>}
      <div className="snapshot-controls"><button disabled={!available||snapshotBusy} onClick={capturePreview}>{snapshotBusy?'Capturing…':'Capture PNG'}</button>{mode==='slice'&&<label className="check-label"><input type="checkbox" checked={includeSnapshotRois} onChange={e=>setIncludeSnapshotRois(e.target.checked)}/> Include visible ROIs</label>}<button disabled={!snapshotDetails} onClick={()=>download(snapshotDetails,'OrganelleScope-snapshot-details.json')}>Export snapshot details</button><span className="hint" role="status">{snapshotMessage||'Capture the displayed view; native pixels remain in the TIFF.'}</span></div>
      {!info ? <div className="empty"><img className="empty-logo" src="./branding/brand-logo.jpg" alt="OrganelleScope — Cellular Exploration & Analysis"/><h2>A clearer view of cellular space.</h2><p>Open a TIFF to inspect its channels, depth and physical calibration.</p><span>TIFF · OME-TIFF · ImageJ TIFF · up to 4 channels</span></div> : !available ? <div className="empty"><h2>Review the image axes</h2><p>Confirm how dimensions map to channels and depth before viewing.</p></div> : mode==="volume" ? <VolumeView contrast={contrast} luts={lutQuery} image={image!} channel={volumeChannel} onChannelChange={setVolumeChannel} captureRef={volumeCapture} maskMesh={projectData['Segmentation.mesh'] as Record<string,any>|undefined}/> : <>
        <div className="slice-toolbar"><label>Z plane <strong>{z+1} / {info.dimensions.Z}</strong><input aria-label="Z plane" type="range" min={0} max={info.dimensions.Z-1} value={z} onChange={e=>{setZ(Number(e.target.value));setRoi(null);}}/></label><span>{info.calibration.Z.value_um != null ? `${(z*info.calibration.Z.value_um).toFixed(3)} µm from first plane` : "Z spacing unknown"}</span></div>

        <PreviewZoom width={info.dimensions.X} height={info.dimensions.Y}><div className="image-stage" ref={snapshotStage} style={{aspectRatio:`${info.dimensions.X}/${info.dimensions.Y}`}}>{preview ? <img src={preview} alt={`Composite Z plane ${z+1}`}/> : <p>Loading source plane…</p>}
          <RoiOverlay spacing={{x:info.calibration.X.value_um,y:info.calibration.Y.value_um}} controlsContainer={drawingActions} disabled={busy || loadingSaved} key={`${image!.id}-${z}-${tool}`} width={info.dimensions.X} height={info.dimensions.Y} z={z} tool={tool} rois={areas} line={roi} onLine={setRoi} onAdd={r=>{if(busy)return;setAreas(a=>[...a,r]);setAnalysis(null);}}/>

        </div></PreviewZoom>
        <div className="drawing-dock" role="toolbar" aria-label="Image drawing tools"><div className="roi-tools"><label>Drawing tool<select aria-label="Drawing tool" disabled={busy} value={tool} onChange={e=>setTool(e.target.value as DrawTool)}><option value="line">Line profiler</option><option value="circle">Circular ROI</option><option value="polygon">Polygonal ROI</option></select></label><span>{tool==='polygon'?'Click vertices, then finish the polygon.':tool==='circle'?'Drag from the center to the circle edge.':'Drag to sample a line.'}</span></div><div ref={setDrawingActions}/></div>
        <p className="hint viewer-note">ROIs belong to their selected Z plane. Preview contrast follows the selected display setting; select raw or processed intensities in ROI measurements below.</p>
      </>}</section>
      <nav className="workspace-nav" aria-label="Workspaces"><button aria-pressed={workspace==='images'} onClick={()=>setWorkspace('images')}>Image & ROI</button><button disabled={!available} aria-pressed={workspace==='processing'} onClick={()=>setWorkspace('processing')}>Background correction</button><button disabled={!available} aria-pressed={workspace==='roi'} onClick={()=>setWorkspace('roi')}>ROI measurements</button><button disabled={!available} aria-pressed={workspace==='associations'} onClick={()=>setWorkspace('associations')}>Channel associations</button><button disabled={!available||!info||info.dimensions.Z<2} aria-pressed={workspace==='volume'} onClick={()=>setWorkspace('volume')}>3D workspace</button><button disabled={!available} aria-pressed={workspace==='validation'} onClick={()=>setWorkspace('validation')}>Validation</button><button aria-pressed={workspace==='evidence'} onClick={()=>setWorkspace('evidence')}>Molecular evidence</button><button aria-pressed={workspace==='batch'} onClick={()=>setWorkspace('batch')}>Batch analysis</button><button aria-pressed={workspace==='assistant'} onClick={()=>setWorkspace('assistant')}>Local assistant</button></nav>
      <div hidden={workspace!=='volume'}>{image && available && info!.dimensions.Z>=2 && <OrthogonalWorkspace luts={lutQuery} key={`orthogonal-${image.id}`} image={image} processing={processing}/>} {image && available && <SegmentationPanel key={`segment-${image.id}`} image={image} processing={processing} rois={areas}/>}</div>
      <div hidden={workspace!=='processing'}>{image && available && <ProcessingPanel luts={lutQuery} key={`processing-${image.id}`} imageId={image.id} z={z} labels={info!.channel_labels} bitDepth={info!.bit_depth} value={processing} disabled={busy||loadingSaved} onChange={config=>{setProcessing(config);setAnalysis(null);if(!isProcessed(config))setMeasurementSource("raw");}}/>}
      </div><div hidden={workspace!=='roi'}>{image && available && <section className="panel statistics"><p className="eyebrow">AREA ANALYSIS</p><h2>ROI measurements</h2><p className="hint">Draw circular or polygonal ROIs above. Each region is measured separately on its own plane.</p>
        <label>Measurement source<select aria-label="Measurement source" disabled={busy||loadingSaved} value={measurementSource} onChange={e=>{const source=e.target.value as 'raw'|'processed';setMeasurementSource(source);setAnalysis(null);if(source==='processed'&&thresholdMode==='costes')setThresholdMode('manual');}}><option value="raw">Raw source intensities</option><option value="processed" disabled={!isProcessed(processing)}>Processed intensities (applied recipe)</option></select></label><p className="hint">This selection applies to line profiles and ROI statistics. Raw images remain visible in the image explorer and 3D preview.</p>
        <div className="roi-list">{areas.map((r,i)=><div key={r.id}>ROI {i+1} · {r.kind} · Z {r.z+1} {r.kind==='circle'&&<CircleSizeEditor roi={r} sx={info!.calibration.X.value_um} sy={info!.calibration.Y.value_um} width={info!.dimensions.X} height={info!.dimensions.Y} disabled={busy||loadingSaved} onChange={updated=>{setAreas(a=>a.map(x=>x.id===r.id?updated:x));setAnalysis(null);}}/>}<button disabled={busy} onClick={()=>{setAreas(a=>a.filter(x=>x.id!==r.id));setAnalysis(null);}}>Delete ROI {i+1}</button></div>)}</div>
        <div className="roi-tools"><label>Threshold method<select disabled={busy} value={thresholdMode} onChange={e=>{setThresholdMode(e.target.value as typeof thresholdMode);setAnalysis(null);}}><option value="costes" disabled={measurementSource==='processed'}>Costes-style automatic (raw only)</option><option value="manual">Manual per channel</option><option value="zero">Zero threshold</option></select></label><label>Regression target<select disabled={busy} value={target} onChange={e=>{setTarget(Number(e.target.value));setAnalysis(null);}}>{info!.channel_labels.map((l,i)=><option key={i} value={i}>{l}</option>)}</select></label></div>
        {thresholdMode==='manual' && info!.channel_labels.map((l,i)=><label key={i}>{l} threshold<input disabled={busy} type="number" min="0" max={2**info!.bit_depth-1} value={thresholds[i]??0} onChange={e=>{setThresholds(t=>Array.from({length:info!.dimensions.C},(_,j)=>j===i?Number(e.target.value):t[j]??0));setAnalysis(null);}}/></label>)}
        <button disabled={busy || loadingSaved || !areas.length || info!.dimensions.C<2} onClick={calculate}>{busy?'Calculating…':'Calculate ROI statistics'}</button><p className="hint">At least two channels are needed. Results and ROI coordinates are saved locally after calculation and included in the export.</p>
      </section>}
      {analysis && <><RoiSummaryPanel analysis={analysis}/><button onClick={()=>setWorkspace('associations')}>View channel association results</button></>}
      </div><div hidden={workspace!=='associations'}>{analysis?<StatisticsPanel analysis={analysis}/>:<section className="panel statistics"><h2>Channel associations</h2><p>Draw regions in the shared preview, then calculate their statistics in ROI measurements.</p><button onClick={()=>setWorkspace('roi')}>Go to ROI measurements</button></section>}</div><div hidden={workspace!=='images'}>
      {image && available && !profile && <section className="panel statistics"><h2>Image & ROI</h2><p>Draw a line in the preview for its intensity profile. Use ROI measurements for region intensities and Channel associations for colocalization statistics.</p></section>}
      {profile && <><SignalChart title={`${measurementSource==='processed'?'Processed':'Source'} intensity profile`} subtitle="Selected measurement intensities · approximate 3 px smoothing for peak widths only" distances={profile.distances} xUnit={profile.unit} yLabel={measurementSource==='processed'?"Processed gray value":"Source gray value"} traces={profile.traces.map((trace,i)=>({...trace,color:lutCss(displayLuts[i])}))}/><div className="widths">{profile.widths.map((w,i)=><span key={i}>{info!.channel_labels[i]} · single-peak FWHM: {w==null?"not available":`${w.toFixed(3)} ${profile.unit}`}</span>)}</div></>}
      </div>
      <div hidden={workspace!=='validation'}>{image && available && <ValidationPanel key={`validation-${image.id}`} image={image} rois={areas} processing={processing} measurementProcessing={selectedProcessing} thresholds={thresholds} thresholdMode={thresholdMode} target={target}/>}</div>
      <div hidden={workspace!=='evidence'}><EvidencePanel/></div>
      <div hidden={workspace!=='assistant'}><AssistantPanel projectId={project?.id??null} context={{image_id:image?.id??null,expected_image_info:image?.info??null,state:{core:snapshot().core,workspaces:Object.fromEntries(Object.entries(projectData).filter(([key])=>!key.startsWith('AssistantPanel.')))}}}/></div>
      </ProjectStateProvider>
      <div hidden={workspace!=='batch'}><BatchPanel/><ProjectStateProvider data={projectData} setData={setProjectData}><ExperimentPanel/></ProjectStateProvider></div>
      <footer><span>Local research analysis · Reproducible reports · AI interpretations require review.</span><span>Source → calibration → measurement</span></footer>
    </main></div></div>;
}
