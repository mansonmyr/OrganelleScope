import {createContext,useCallback,useContext,useState,useRef,useEffect} from 'react';
import type {Dispatch,SetStateAction,ReactNode} from 'react';
export type WorkspaceData=Record<string,unknown>;
const Context=createContext<{data:WorkspaceData;update:(key:string,initial:unknown,action:unknown)=>void}|null>(null);
export function ProjectStateProvider({data,setData,children}:{data:WorkspaceData;setData:Dispatch<SetStateAction<WorkspaceData>>;children:ReactNode}){
 const active=useRef(true);useEffect(()=>{active.current=true;return()=>{active.current=false;};},[]);
 const update=useCallback((key:string,initial:unknown,action:unknown)=>{if(active.current)setData(previous=>({...previous,[key]:typeof action==='function'?(action as (value:unknown)=>unknown)(previous[key]??initial):action}));},[setData]);
 return <Context.Provider value={{data,update}}>{children}</Context.Provider>;
}
export function useProjectState<T>(key:string):[T|undefined,Dispatch<SetStateAction<T|undefined>>];
export function useProjectState<T>(key:string,initial:T|(()=>T)):[T,Dispatch<SetStateAction<T>>];
export function useProjectState<T>(key:string,initial?:T|(()=>T)):[T|undefined,Dispatch<SetStateAction<T|undefined>>]{
 const [fallback,setFallback]=useState(initial);const context=useContext(Context);const update=context?.update;
 const setter=useCallback<Dispatch<SetStateAction<T|undefined>>>(action=>{if(update)update(key,fallback,action);else setFallback(action);},[update,key,fallback]);
 return [context&&Object.prototype.hasOwnProperty.call(context.data,key)?context.data[key] as T:fallback,setter];
}
