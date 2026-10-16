import { spawnSync } from 'node:child_process';
import { mkdir, mkdtemp, readdir, copyFile } from 'node:fs/promises';
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
const result=spawnSync(process.execPath,[cli,...(mac?['--mac','--arm64']:['--win','--x64']),'--publish','never',`--config.directories.output=${output}`],{cwd:root,stdio:'inherit'});
if(result.status!==0)process.exit(result.status??1);
if(mac){
 const destination=path.join(root,'release');await mkdir(destination,{recursive:true});
 for(const file of await readdir(output))if(file.endsWith('.dmg'))await copyFile(path.join(output,file),path.join(destination,file));
 console.log(`Signed app staging directory: ${output}`);
 console.log(`Mac installers copied to ${destination}`);
}
