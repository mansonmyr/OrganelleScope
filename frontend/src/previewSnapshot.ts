import type {MutableRefObject} from 'react';
export type VolumeCapture={dataUrl:string;details:Record<string,unknown>};
export type VolumeCaptureRef=MutableRefObject<(()=>Promise<VolumeCapture>)|null>;
export async function sliceSnapshot(stage:HTMLElement,includeOverlays:boolean):Promise<string>{
 const source=stage.querySelector('img');
 if(!source?.complete||!source.naturalWidth)throw new Error('Wait for the image preview to finish loading.');
 const canvas=document.createElement('canvas');canvas.width=source.naturalWidth;canvas.height=source.naturalHeight;
 const context=canvas.getContext('2d');if(!context)throw new Error('Image export is unavailable.');
 context.drawImage(source,0,0);
 const overlay=stage.querySelector('svg');
 if(includeOverlays&&overlay){
  const copy=overlay.cloneNode(true) as SVGSVGElement;copy.setAttribute('xmlns','http://www.w3.org/2000/svg');copy.setAttribute('width',String(canvas.width));copy.setAttribute('height',String(canvas.height));
  const href=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(copy)],{type:'image/svg+xml'}));
  try{const drawing=new Image();await new Promise<void>((resolve,reject)=>{drawing.onload=()=>resolve();drawing.onerror=()=>reject(new Error('ROI overlay export failed.'));drawing.src=href;});context.drawImage(drawing,0,0);}finally{URL.revokeObjectURL(href);}
 }
 return canvas.toDataURL('image/png');
}
export function downloadSnapshot(dataUrl:string,name:string){const link=document.createElement('a');link.href=dataUrl;link.download=name;link.click();}
