import { spawnSync } from 'node:child_process';
import { mkdir, mkdtemp, readdir, copyFile,writeFile,readFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
// File-provider-managed Documents folders can add FinderInfo to .app bundles after cleanup.
// Build macOS apps in temporary storage; copy only finished installer files back to the project.
const mac=process.platform==='darwin';
if(!mac && process.platform!=='win32')throw new Error('Build desktop installers on macOS or Windows.');
const output=mac?await mkdtemp(path.join(os.tmpdir(),'OrganelleScope-package-')):path.join(root,'release');
const cli=path.join(root,'node_modules','electron-builder','cli.js');
const python=process.env.ORGANELLESCOPE_PYTHON||(process.platform==='win32'?'python':'python3');
const runtime=spawnSync(python,['scripts/setup-local-assistant.py','--runtime-only','--download'],{cwd:root,stdio:'inherit'});
if(runtime.status!==0)process.exit(runtime.status??1);
const notices=spawnSync(python,['scripts/dependency-notices.py'],{cwd:root,stdio:'inherit'});
if(notices.status!==0)process.exit(notices.status??1);
const fullAI=process.env.ORGANELLESCOPE_INCLUDE_ASSISTANT==='1';
const extra=[];
if(fullAI){
 const {createHash}=await import('node:crypto');const {createReadStream}=await import('node:fs');const model=path.join(root,'.local-models','gemma-4-12b-it-qat-q4_0.gguf');
 const hash=createHash('sha256');for await(const chunk of createReadStream(model))hash.update(chunk);
 if(hash.digest('hex')!=='93567e57a8fe10b23569b9d9ec38cd005deedf71e29477c421a4b83f418a538b')throw new Error('Bundled model checksum mismatch.');
 const configuration=JSON.parse(await readFile(path.join(root,'package.json'),'utf8')).build;
 configuration.extraResources.push({from:'.local-models',to:'local-ai/model',filter:['gemma-4-12b-it-qat-q4_0.gguf']});
 const configPath=path.join(root,'build','offline-desktop.json');await mkdir(path.dirname(configPath),{recursive:true});await writeFile(configPath,JSON.stringify(configuration));extra.push('--config',configPath);
}
const result=spawnSync(process.execPath,[cli,...extra,...(mac?['--mac','--arm64']:['--win','--x64']),'--publish','never',`--config.directories.output=${output}`],{cwd:root,stdio:'inherit'});
if(result.status!==0)process.exit(result.status??1);
if(mac){
 const destination=path.join(root,'release');await mkdir(destination,{recursive:true});
 for(const file of await readdir(output))if(file.endsWith('.dmg'))await copyFile(path.join(output,file),path.join(destination,file));
 console.log(`Signed app staging directory: ${output}`);
 console.log(`Mac installers copied to ${destination}`);
}
