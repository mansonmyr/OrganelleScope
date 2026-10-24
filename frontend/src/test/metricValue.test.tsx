import React from 'react';
import {afterEach,beforeEach,it,expect,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {MetricValue} from '../MetricValue';
import {ProcessingHelp} from '../ProcessingHelp';
beforeEach(()=>{HTMLDialogElement.prototype.showModal=vi.fn(function(this:HTMLDialogElement){this.open=true;});});
afterEach(cleanup);
it('explains an unavailable value and preserves a real zero as numeric zero',()=>{
 render(<><MetricValue value={null} reason="Channel B contains only zeros; the denominator is zero." label="A / B Pearson"/><MetricValue value={0} label="A / B M1"/></>);
 fireEvent.click(screen.getByRole('button',{name:'Why A / B Pearson is unavailable'}));
 expect(screen.getByRole('dialog').textContent).toContain('Channel B contains only zeros');expect(screen.getByText('0')).toBeTruthy();
});
it('opens source-linked background guidance and distinguishes square opening from rolling ball',()=>{
 render(<ProcessingHelp/>);fireEvent.click(screen.getByRole('button',{name:'About background correction and defaults'}));
 expect(screen.getByRole('dialog').textContent).toContain('Curved-kernel lower envelope');
 expect(screen.getByRole('link',{name:'ImageJ: rolling-ball radius guidance'}).getAttribute('href')).toBe('https://imagej.net/plugins/rolling-ball-background-subtraction');
});

it('explains legacy report blanks from its recorded channel statistics',async()=>{
 const {metricReason}=await import('../MetricValue');
 const pair={label_a:'A',label_b:'B'},channels=[{label:'A',std:2,sum:30},{label:'B',std:0,sum:0}];
 expect(metricReason('pcc',pair,channels)).toContain('B contains only zero intensities');
 expect(metricReason('m2',pair,channels)).toContain('zero denominator');
 expect(metricReason('m1',pair,channels)).toBeUndefined();
});
