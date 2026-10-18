// Fail packaging if private research storage appears in the generated payload.
const fs=require('node:fs');
const path=require('node:path');
const forbiddenDirectory=/^(?:local-samples|sample images?|batch-data|project-data|evidence-cache)$/i;
const forbiddenFile=/^(?:source\.tiff?|recovery-latest\.json)$/i;
function auditTree(root){
 const inspected=[];
 function visit(folder){for(const entry of fs.readdirSync(folder,{withFileTypes:true})){
  const file=path.join(folder,entry.name);
  if(entry.isSymbolicLink())continue;
  if(entry.isDirectory()){if(forbiddenDirectory.test(entry.name))throw new Error('Research storage in installer: '+file);visit(file);}
  else if(forbiddenFile.test(entry.name)||/\.tiff?$/i.test(entry.name))throw new Error('Research data in installer: '+file);
  inspected.push(path.relative(root,file));
 }}
 visit(root);return inspected.length;
}
function auditArchive(entries){
 for(const file of entries){
  const pieces=file.split(/[\\/]/).filter(Boolean);
  if(pieces.some(piece=>forbiddenDirectory.test(piece))||pieces.some(piece=>forbiddenFile.test(piece))||/\.tiff?$/i.test(file))throw new Error('Research data in application archive: '+file);
 }
 return entries.length;
}
module.exports={auditTree,auditArchive};
