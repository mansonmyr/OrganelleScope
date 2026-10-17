import React from 'react';
import {afterEach,it,expect,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {CircleSizeEditor} from '../CircleSizeEditor';
afterEach(cleanup);
const roi={id:'r',kind:'circle' as const,z:0,points:[{x:50,y:50},{x:60,y:50}]};
it('edits diameter in micrometers without moving the center and rejects missing scale',()=>{
 const onChange=vi.fn();const view=render(<CircleSizeEditor roi={roi} sx={.1} sy={.2} width={100} height={100} disabled={false} onChange={onChange}/>);
 fireEvent.change(screen.getByLabelText('Diameter in micrometers for r'),{target:{value:'3'}});fireEvent.click(screen.getByText('Apply diameter'));
 expect(onChange).toHaveBeenCalledWith({...roi,diameter_um:3,points:[{x:50,y:50},{x:65,y:50}]});
 view.rerender(<CircleSizeEditor roi={roi} sx={null} sy={.2} width={100} height={100} disabled={false} onChange={onChange}/>);
 expect((screen.getByText('Apply diameter') as HTMLButtonElement).disabled).toBe(true);
});
