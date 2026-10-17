import {it,expect} from 'vitest';
import {hasRetiredProcessing,rawProcessingCopy} from '../retiredProcessing';
it('opens a recalculation copy without altering historical reports or ROIs',()=>{
 const state={core:{areas:[{id:'roi',z:2}],analysis:{processing:{restoration_result_id:'old'},value:12},processing:{background:'constant',offsets:[10,20],radius_px:20,sigma_px:1,restoration_result_id:'old'}},workspaces:{'Segmentation.report':{sum:55}}};
 const before=JSON.stringify(state);expect(hasRetiredProcessing(state)).toBe(true);
 const copy=rawProcessingCopy(state);expect(copy.core.analysis).toBeNull();expect(copy.workspaces).toEqual({});expect(copy.core.areas).toEqual(state.core.areas);expect(copy.core.processing).toEqual({background:'constant',offsets:[10,20],radius_px:20,sigma_px:1});expect(copy.core.measurementSource).toBe('processed');expect(JSON.stringify(state)).toBe(before);
});
it('keeps ordinary Gaussian/background recipes supported',()=>{
 expect(hasRetiredProcessing({processing:{background:'rolling_ball',sigma_px:1,restoration_result_id:null}})).toBe(false);
});
