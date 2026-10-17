/** Linear black-to-colour display maps; independent of quantitative intensities. */
export const LUTS={rose:{label:'Rose',rgb:[1,.12,.25]},mint:{label:'Mint',rgb:[.1,1,.65]},ocean:{label:'Ocean',rgb:[.2,.45,1]},silver:{label:'Silver',rgb:[.8,.8,.8]},red:{label:'Red',rgb:[1,0,0]},green:{label:'Green',rgb:[0,1,0]},blue:{label:'Blue',rgb:[0,0,1]},cyan:{label:'Cyan',rgb:[0,1,1]},magenta:{label:'Magenta',rgb:[1,0,1]},yellow:{label:'Yellow',rgb:[1,1,0]},gray:{label:'Grayscale',rgb:[1,1,1]},orange:{label:'Orange',rgb:[1,.49,0]}} as const;
export type LutName=keyof typeof LUTS;
export const DEFAULT_LUTS:LutName[]=['rose','mint','ocean','silver'];
export function channelLuts(saved:unknown,count:number):LutName[]{return Array.from({length:count},(_,i)=>Array.isArray(saved)&&Object.prototype.hasOwnProperty.call(LUTS,saved[i])?saved[i]:DEFAULT_LUTS[i]);}
export function lutColor(name:LutName):[number,number,number]{return [...LUTS[name].rgb];}
export function lutCss(name:LutName):string{return `rgb(${LUTS[name].rgb.map(v=>Math.round(v*255)).join(',')})`;}
