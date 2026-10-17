import {it,expect} from 'vitest';
import {translateCuboid,centerCuboid,initialCuboid,cuboidCenter} from '../cuboidMovement';
it('moves within all axes, clamps to source edges and preserves inclusive voxel count',()=>{
 const b={x0:2,x1:5,y0:3,y1:6,z0:1,z1:2},d={X:12,Y:14,Z:6};
 expect(translateCuboid(b,{X:3,Y:-99,Z:99},d)).toEqual({x0:5,x1:8,y0:0,y1:3,z0:4,z1:5});
 const next=centerCuboid(b,{X:11,Y:13,Z:5},d);expect(next).toEqual({x0:8,x1:11,y0:10,y1:13,z0:4,z1:5});
 expect((next.x1-next.x0+1)*(next.y1-next.y0+1)*(next.z1-next.z0+1)).toBe(32);
 expect(b.x0).toBe(2);
});
it('starts near the specimen center instead of an unexplained corner and keeps full Z',()=>{
 const b=initialCuboid({X:370,Y:370,Z:36});expect(b).toEqual({x0:153,x1:216,y0:153,y1:216,z0:0,z1:35});expect(cuboidCenter(b)).toEqual({X:184,Y:184,Z:17});
});
