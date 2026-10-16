import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { RoiOverlay } from '../RoiOverlay';
import type { AreaROI } from '../RoiOverlay';

beforeEach(()=>{
  vi.stubGlobal('PointerEvent',MouseEvent);
  Object.defineProperty(SVGSVGElement.prototype,'createSVGPoint',{configurable:true,value(){return {x:0,y:0,matrixTransform(){return {x:this.x,y:this.y};}};}});
  Object.defineProperty(SVGSVGElement.prototype,'getScreenCTM',{configurable:true,value:()=>({inverse:()=>({})})});
  Object.defineProperty(SVGSVGElement.prototype,'setPointerCapture',{configurable:true,value:()=>{}});
  Object.defineProperty(SVGSVGElement.prototype,'hasPointerCapture',{configurable:true,value:()=>false});
});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
const base={width:100,height:100,z:3,rois:[] as AreaROI[],line:null,onLine:vi.fn()};
function click(x:number,y:number){fireEvent.pointerDown(screen.getByLabelText('ROI drawing surface'),{clientX:x,clientY:y,button:0});}

describe('area drawing workflow',()=>{
  it('completes a circle only on release and keeps its Z plane',()=>{
    const onAdd=vi.fn();render(<RoiOverlay {...base} tool="circle" onAdd={onAdd}/>);
    click(20,20);expect(onAdd).not.toHaveBeenCalled();
    fireEvent.pointerMove(screen.getByLabelText('ROI drawing surface'),{clientX:30,clientY:20});
    fireEvent.pointerUp(screen.getByLabelText('ROI drawing surface'),{clientX:30,clientY:20});
    expect(onAdd).toHaveBeenCalledWith(expect.objectContaining({kind:'circle',z:3,points:[{x:20,y:20},{x:30,y:20}]}));
  });
  it('does not accidentally save a two-vertex polygon; finishes explicitly',()=>{
    const onAdd=vi.fn();render(<RoiOverlay {...base} tool="polygon" onAdd={onAdd}/>);
    click(10,10);click(30,10);
    expect((screen.getByText('Finish polygon (2)') as HTMLButtonElement).disabled).toBe(true);
    expect(onAdd).not.toHaveBeenCalled();click(20,30);
    fireEvent.click(screen.getByText('Finish polygon (3)'));
    expect(onAdd).toHaveBeenCalledWith(expect.objectContaining({kind:'polygon',z:3,points:[{x:10,y:10},{x:30,y:10},{x:20,y:30}]}));
  });
  it('shows only ROIs on the current plane and disables new drawings during calculation',()=>{
    const onAdd=vi.fn();const rois:AreaROI[]=[{id:'a',kind:'circle',z:3,points:[{x:20,y:20},{x:30,y:20}]},{id:'b',kind:'circle',z:2,points:[{x:40,y:40},{x:50,y:40}]}];
    const {container}=render(<RoiOverlay {...base} rois={rois} tool="circle" onAdd={onAdd} disabled/>);
    expect(container.querySelectorAll('circle').length).toBe(1);
    click(10,10);fireEvent.pointerUp(screen.getByLabelText('ROI drawing surface'),{clientX:30,clientY:20});expect(onAdd).not.toHaveBeenCalled();
  });
});
