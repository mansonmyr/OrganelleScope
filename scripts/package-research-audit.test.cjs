const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const os=require('node:os');const path=require('node:path');const {auditTree,auditArchive}=require('./package-research-audit.cjs');
test('installer audit rejects private source TIFFs and recovery records, allows UI assets',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'OrganelleScope-payload-'));
 try{fs.mkdirSync(path.join(dir,'images'));fs.writeFileSync(path.join(dir,'images','icon.png'),'icon');assert.ok(auditTree(dir));
 for(const name of ['source.tiff','private-microscopy.tif','recovery-latest.json']){const p=path.join(dir,name);fs.writeFileSync(p,'private');assert.throws(()=>auditTree(dir),/Research data/);fs.unlinkSync(p);}
 fs.mkdirSync(path.join(dir,'batch-data'));assert.throws(()=>auditTree(dir),/Research storage/);
 assert.throws(()=>auditArchive(['/frontend/dist/app.js','/local-samples/specimen.tif']),/Research data/);
 assert.ok(auditArchive(['/frontend/dist/assets/icon.png','/electron/main.cjs']));
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
