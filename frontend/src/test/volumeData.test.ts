import { expect,it } from 'vitest';
import { interleaveChannels } from '../volumeData';
it('preserves voxel/channel ordering for four-channel volume compositing',()=>{
 const channels=[[10,11,12],[20,21,22],[30,31,32],[40,41,42]].map(v=>new Uint16Array(v));
 expect(Array.from(interleaveChannels(channels))).toEqual([10,20,30,40,11,21,31,41,12,22,32,42]);
 expect(Array.from(channels[0])).toEqual([10,11,12]);
 expect(interleaveChannels([channels[0]])).toBe(channels[0]);
 expect(()=>interleaveChannels([channels[0],new Uint16Array(1)])).toThrow('matching geometry');
});
