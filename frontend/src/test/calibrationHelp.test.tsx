import React from 'react';
import {fireEvent,render,screen,cleanup} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {CalibrationHelp} from '../CalibrationHelp';
afterEach(cleanup);
it('opens a keyboard-accessible explanation distinguishing sampling from resolution',()=>{
 const show=vi.fn();Object.defineProperty(HTMLDialogElement.prototype,'showModal',{configurable:true,value:show});
 render(<CalibrationHelp/>);fireEvent.click(screen.getByRole('button',{name:'About physical calibration'}));
 expect(show).toHaveBeenCalledOnce();
 expect(screen.getByText(/31 slices/).textContent).toContain('9.0 µm');
 expect(screen.getByText(/Calibration is different from optical resolution/)).toBeTruthy();
 expect(screen.getByText(/voxel-space preview/)).toBeTruthy();
});
