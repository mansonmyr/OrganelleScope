/** Interleave native channel values at each voxel for a single multicomponent ray-cast volume. */
export function interleaveChannels(channels: Uint16Array[]): Uint16Array {
  if(!channels.length || channels.length>4 || channels.some(c=>c.length!==channels[0].length))throw new Error('Volume channels must have matching geometry and contain one to four components.');
  if(channels.length===1)return channels[0];
  const result=new Uint16Array(channels[0].length*channels.length);
  for(let i=0;i<channels[0].length;i++)for(let c=0;c<channels.length;c++)result[i*channels.length+c]=channels[c][i];
  return result;
}

/** Keep even a diagonal ray inside the renderer's 1,000-sample limit. */
export function volumeSampleDistance(shape:number[],spacing:number[],stretch:number):number {
  const diagonal=Math.hypot((shape[2]-1)*spacing[0],(shape[1]-1)*spacing[1],(shape[0]-1)*spacing[2]*stretch);
  return Math.max(Math.min(...spacing)/2,diagonal/900);
}
