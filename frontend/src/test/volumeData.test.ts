import { expect,it } from 'vitest';
import { interleaveChannels, volumeSampleDistance } from '../volumeData';
it('preserves voxel/channel ordering for four-channel volume compositing',()=>{
 const channels=[[10,11,12],[20,21,22],[30,31,32],[40,41,42]].map(v=>new Uint16Array(v));
 expect(Array.from(interleaveChannels(channels))).toEqual([10,20,30,40,11,21,31,41,12,22,32,42]);
 expect(Array.from(channels[0])).toEqual([10,11,12]);
 expect(interleaveChannels([channels[0]])).toBe(channels[0]);
 expect(()=>interleaveChannels([channels[0],new Uint16Array(1)])).toThrow('matching geometry');
});

it('keeps shallow anisotropic stacks and stretched views within the ray budget',()=>{
 for(const stretch of [1,5,10]){
  const shape=[15,125,110], spacing=[1.575,.63,.315];
  const step=volumeSampleDistance(shape,spacing,stretch);
  const longestRay=Math.hypot(109*1.575,124*.63,14*.315*stretch);
  expect(Math.ceil(longestRay/step)).toBeLessThanOrEqual(1000);
  expect(step).toBeGreaterThanOrEqual(.315/2);
 }
});
