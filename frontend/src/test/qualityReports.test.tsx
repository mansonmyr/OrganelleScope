import React from 'react';
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import {ProximityReport} from '../ProximityReport';
import {RoiSummaryPanel} from '../RoiSummaryPanel';
import {AnalysisHistory} from '../AnalysisHistory';
import {json} from '../api';
vi.mock('../api',()=>({json:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
it('shows ROI ceiling counts with the regional denominator',()=>{
 const channel={label:'A',mean:100,sum:900,std:5,raw_quality:{ceiling_samples:4,sample_count:9},estimated_background:{min:2,max:6,std:1}};
 render(<RoiSummaryPanel analysis={{scope:'raw',results:[{roi:{id:'r',kind:'circle',z:0},pixel_count:9,area_um2:1,channel_summary:[channel],warnings:[]}]} as any}/>);
 expect(screen.getByText('4 / 9')).toBeTruthy();expect(screen.getByText('2–6 / 1')).toBeTruthy();
});
it('shows occupancy and sampling warnings before proximity interpretation details',()=>{
 render(<ProximityReport report={{distance_threshold_um:.25,mask_occupancy:{cuboid_voxels:100,marker_fraction:.2,reference_fraction:.8},sampling_review:{z_step_um:.4,z_planes:4},quality_warnings:['The near-distance cutoff is smaller than the Z step.']}}/>);
 expect(screen.getByText(/Cuboid occupancy: marker 20%/)).toBeTruthy();expect(screen.getByText('The near-distance cutoff is smaller than the Z step.')).toBeTruthy();
});
it('handles an unexpected history response without losing the current workspace',async()=>{
 vi.mocked(json).mockResolvedValue({unexpected:'response'});
 render(<AnalysisHistory imageId="x"/>);
 expect(await screen.findByText('The report history response could not be read. Existing reports are unchanged.')).toBeTruthy();
});
