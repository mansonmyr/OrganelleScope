import React from 'react';
import {afterEach,expect,it} from 'vitest';
import {cleanup,render,screen,within} from '@testing-library/react';
import {ProximityReport} from '../ProximityReport';
afterEach(cleanup);
it('keeps the directed denominators and undefined results explicit',()=>{
 const direction={source_voxels:20,within_distance_voxels:5,fraction_within_distance:.25,nearest_occupied_voxel_center_um:0,median_occupied_voxel_center_um:2,p95_occupied_voxel_center_um:4};
 render(<ProximityReport report={{distance_threshold_um:.5,marker_to_reference:direction,reference_to_marker:{...direction,source_voxels:5,within_distance_voxels:5,fraction_within_distance:1}}}/>);
 const forward=screen.getByText('Marker → reference').closest('tr')!;
 const reverse=screen.getByText('Reference → marker').closest('tr')!;
 expect(within(forward).getByText('20')).toBeTruthy();
 expect(within(forward).getByText('0.25')).toBeTruthy();
 expect(within(reverse).getByText('1')).toBeTruthy();
 cleanup();render(<ProximityReport report={{unavailable_reason:'Reference mask is empty.'}}/>);
 expect(screen.getByText('Proximity unavailable: Reference mask is empty.')).toBeTruthy();
 expect(screen.queryByRole('table')).toBeNull();
});
