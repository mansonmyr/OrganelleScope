import {expect,it} from 'vitest';
import {analyzeStoredImage,buildChannelMetrics,makeParsedImage,sampleTrace} from '../workers/analysisCore';
it('withholds widths when a raw clipped peak remains hidden by processed values',()=>{
 const raw=Uint16Array.from({length:61},(_,i)=>Math.min(65535,Math.round(90000*Math.exp(-(((i-30)/7)**2)))));
 const processed=Float32Array.from(raw,v=>v-1000);
 const image=makeParsedImage('r','r.tif',61,1,[raw,raw]);
 const stored={image,rawChannels:[raw,raw],activeChannels:[processed,processed],preprocessing:{enabled:false,rollingBallRadius:20}};
 const result=analyzeStoredImage(stored,{start:{x:0,y:0},end:{x:60,y:0},sampleSpacingPx:1},{pixelSize:.065,unit:'um'});
 for(const metric of result.profile.metrics){expect(metric.quality?.rawCeilingSampleCount).toBeGreaterThan(0);expect(metric.quality?.fwhmWithheld).toBe(true);expect(metric.peaks.every(p=>p.fwhmPhysical===null)).toBe(true);}
});
it('detects a ceiling contributor before bilinear interpolation hides it',()=>{
 const trace=sampleTrace(new Uint16Array([65535,0,0,0]),4,1,{start:{x:.5,y:0},end:{x:2.5,y:0},sampleSpacingPx:1},'A','red');
 expect(trace.rawValues[0]).toBe(32767.5);
 const result=buildChannelMetrics(trace,trace.distancesPx,trace.distancesPx,'um');
 expect(result.quality?.rawCeilingSampleCount).toBe(1);expect(result.quality?.fwhmWithheld).toBe(true);
});
it('leaves an unsaturated Gaussian width available',()=>{
 const raw=Uint16Array.from({length:61},(_,i)=>Math.round(50000*Math.exp(-(((i-30)/7)**2))));
 const trace=sampleTrace(raw,61,1,{start:{x:0,y:0},end:{x:60,y:0},sampleSpacingPx:1},'A','red');
 const result=buildChannelMetrics(trace,trace.distancesPx,trace.distancesPx,'um');
 expect(result.quality?.fwhmWithheld).toBe(false);expect(result.peaks[0].fwhmPx).not.toBeNull();
});
