import React from 'react';
import {afterEach,it,expect} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {PreviewZoom} from '../PreviewZoom';
afterEach(cleanup);
it('limits zoom, fits aspect ratio and preserves the source stage',()=>{
 render(<PreviewZoom width={100} height={50}><div className="image-stage"><svg viewBox="0 0 100 50"><circle cx="20" cy="10" r="5"/></svg></div></PreviewZoom>);
 const panel=screen.getByLabelText('Zoomable XY image'),circle=panel.querySelector('circle')!;
 expect(panel.style.getPropertyValue('--preview-width')).toBe('650px');expect(panel.style.getPropertyValue('--preview-height')).toBe('325px');
 fireEvent.change(screen.getByRole('slider',{name:'XY preview zoom'}),{target:{value:'800'}});expect((screen.getByRole('button',{name:'Zoom in XY preview'}) as HTMLButtonElement).disabled).toBe(true);expect(panel.style.getPropertyValue('--preview-width')).toBe('5200px');
 expect(panel.querySelector('circle')).toBe(circle);expect(circle.getAttribute('cx')).toBe('20');
 fireEvent.change(screen.getByRole('slider',{name:'XY preview zoom'}),{target:{value:'25'}});expect((screen.getByRole('button',{name:'Zoom out XY preview'}) as HTMLButtonElement).disabled).toBe(true);
 fireEvent.click(screen.getByRole('button',{name:'Fit image'}));expect(panel.style.getPropertyValue('--preview-width')).toBe('650px');
});
it('consumes trackpad pinch and wheel zoom while preserving ROI coordinates',()=>{
 render(<PreviewZoom width={100} height={50}><div className="image-stage"><svg viewBox="0 0 100 50"><circle cx="20" cy="10" r="5"/></svg></div></PreviewZoom>);
 const panel=screen.getByLabelText('Zoomable XY image'),stage=panel.querySelector<HTMLElement>('.image-stage')!;
 Object.defineProperties(panel,{clientWidth:{value:650},clientHeight:{value:450}});
 Object.defineProperties(stage,{offsetWidth:{get:()=>parseFloat(panel.style.getPropertyValue('--preview-width'))},offsetHeight:{get:()=>parseFloat(panel.style.getPropertyValue('--preview-height'))},offsetLeft:{value:0},offsetTop:{value:0}});
 expect(fireEvent.wheel(panel,{deltaY:-50,ctrlKey:true,clientX:200,clientY:100})).toBe(false);
 expect((screen.getByRole('slider',{name:'XY preview zoom'}) as HTMLInputElement).value).toBe('165');
 expect(panel.scrollLeft).toBeCloseTo(130);expect(panel.scrollTop).toBeCloseTo(65);
 fireEvent.wheel(panel,{deltaY:100});expect(Number((screen.getByRole('slider',{name:'XY preview zoom'}) as HTMLInputElement).value)).toBeLessThan(165);
 expect(stage.querySelector('circle')!.getAttribute('cx')).toBe('20');expect(stage.querySelector('svg')!.getAttribute('viewBox')).toBe('0 0 100 50');
});
it('pans with explicit pan mode or space without forwarding a drawing gesture',()=>{
 let drawings=0;
 render(<PreviewZoom width={100} height={50}><div className="image-stage" onPointerDown={()=>drawings++}/></PreviewZoom>);
 const panel=screen.getByLabelText('Zoomable XY image'),stage=panel.querySelector('.image-stage')!;
 // jsdom does not provide PointerEvent; these events carry the native pointer properties.
 function pointer(type:string,x:number,y:number){const event=new Event(type,{bubbles:true,cancelable:true});Object.assign(event,{pointerId:1,button:0,clientX:x,clientY:y});fireEvent(stage,event);}
 fireEvent.click(screen.getByRole('button',{name:'Pan image'}));
 panel.scrollLeft=200;panel.scrollTop=100;pointer('pointerdown',150,100);pointer('pointermove',100,70);pointer('pointerup',100,70);
 expect(panel.scrollLeft).toBe(250);expect(panel.scrollTop).toBe(130);expect(drawings).toBe(0);
 fireEvent.click(screen.getByRole('button',{name:'Pan image'}));pointer('pointerdown',100,70);expect(drawings).toBe(1);
 fireEvent.keyDown(panel,{code:'Space'});pointer('pointerdown',100,70);pointer('pointermove',80,60);pointer('pointerup',80,60);fireEvent.keyUp(panel,{code:'Space'});
 expect(panel.scrollLeft).toBe(270);expect(drawings).toBe(1);
});
