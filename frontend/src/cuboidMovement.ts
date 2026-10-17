export type Position={X:number;Y:number;Z:number};
export type Bounds={x0:number;x1:number;y0:number;y1:number;z0:number;z1:number};
export function translateCuboid(bounds:Bounds,delta:Partial<Position>,dimensions:Record<string,number>):Bounds{
 const moved={...bounds} as Record<string,number>;
 for(const axis of ['X','Y','Z'] as const){
  const a=axis.toLowerCase(),start=moved[a+'0'],end=moved[a+'1'],shift=delta[axis]??0;
  if(!Number.isInteger(start)||!Number.isInteger(end)||start<0||end<start||end>=dimensions[axis]||!Number.isFinite(shift))return bounds;
  const step=Math.max(-start,Math.min(dimensions[axis]-1-end,Math.round(shift)));
  moved[a+'0']=start+step;moved[a+'1']=end+step;
 }
 return moved as Bounds;
}
export function cuboidCenter(bounds:Bounds):Position{return {X:Math.floor((bounds.x0+bounds.x1)/2),Y:Math.floor((bounds.y0+bounds.y1)/2),Z:Math.floor((bounds.z0+bounds.z1)/2)};}
export function centerCuboid(bounds:Bounds,position:Partial<Position>,dimensions:Record<string,number>):Bounds{
 const center=cuboidCenter(bounds),delta:Partial<Position>={};
 for(const axis of ['X','Y','Z'] as const)if(position[axis]!=null)delta[axis]=position[axis]!-center[axis];
 return translateCuboid(bounds,delta,dimensions);
}
export function initialCuboid(dimensions:Record<string,number>):Bounds{
 const b={} as Record<string,number>;
 for(const axis of ['X','Y','Z'] as const){const a=axis.toLowerCase(),size=axis==='Z'?dimensions[axis]:Math.min(dimensions[axis],64);b[a+'0']=Math.floor((dimensions[axis]-size)/2);b[a+'1']=b[a+'0']+size-1;}
 return b as Bounds;
}
