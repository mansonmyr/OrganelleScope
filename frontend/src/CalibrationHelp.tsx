import { useRef } from 'react';
export function CalibrationHelp() {
  const dialog=useRef<HTMLDialogElement>(null);
  return <><button type="button" className="info-button" aria-label="About physical calibration" onClick={()=>dialog.current?.showModal()}>ⓘ What does this mean?</button>
    <dialog ref={dialog} aria-labelledby="calibration-title" className="calibration-dialog" onClick={e=>{if(e.target===dialog.current){const r=dialog.current!.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.current?.close();}}}>
      <h2 id="calibration-title">Physical calibration: giving pixels a real size</h2>
      <p>A TIFF contains a grid of pixels and Z slices. Calibration tells the application how far apart those samples are in the specimen, so the 3D volume has the correct proportions and distances can be reported in micrometres (µm).</p>
      <dl><dt>X / Y pixel spacing</dt><dd>The specimen distance between neighboring pixel centers across and down the image.</dd><dt>Z spacing (Z-step)</dt><dd>The distance between consecutive optical sections. This is not the total thickness of the sample.</dd></dl>
      <p>Example only: X = 0.10 µm, Y = 0.10 µm, Z = 0.30 µm means each Z step is three times the lateral pixel spacing. For 31 slices, the distance from the first to the last slice is 30 × 0.30 = 9.0 µm.</p>
      <p>OrganelleScope reads supported TIFF metadata automatically. If a value is missing or conflicting, check the acquisition metadata or ask the imaging facility. Use the effective specimen pixel size for that acquisition, including objective magnification, zoom and binning. Camera sensor pixel size or print DPI alone is insufficient. 1 µm = 1,000 nm.</p>
      <p>Calibration is different from optical resolution. Smaller pixels or denser Z sampling do not by themselves reveal smaller structures or turn conventional microscopy into super-resolution data.</p>
      <p>When spacing is unknown, a clearly labeled voxel-space preview is available. Its proportions are based on pixel/slice counts; physical shape and distances cannot be established until X, Y and Z are confirmed. A single XY image has no measured Z volume.</p>
      <form method="dialog"><button autoFocus>Close explanation</button></form>
    </dialog></>;
}
