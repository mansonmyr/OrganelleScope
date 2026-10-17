import {rawProcessing,isProcessed} from './ProcessingPanel';
export function hasRetiredProcessing(value:unknown):boolean{
 if(Array.isArray(value))return value.some(hasRetiredProcessing);
 if(value&&typeof value==='object'){
  const record=value as Record<string,unknown>;
  if(record.restoration_result_id)return true;
  return Object.values(record).some(hasRetiredProcessing);
 }
 return false;
}
export function rawProcessingCopy(state:Record<string,any>){
 const core=state.core??{};
 const {restoration_result_id,...processing}={...rawProcessing,...core.processing};
 return {...state,core:{...core,processing,analysis:null,measurementSource:isProcessed(processing)?'processed':'raw'},workspaces:{}};
}
