const path = require('node:path');
const { spawnSync } = require('node:child_process');

module.exports = async function prepareMacSignature(context) {
  const {auditTree,auditArchive}=require('./package-research-audit.cjs');
  auditTree(context.appOutDir);
  // Inspect the application archive too; directory scanning cannot see ASAR contents.
  const {listPackage}=require('@electron/asar');
  const fs=require('node:fs');
  const resources=context.electronPlatformName==='darwin'?path.join(context.appOutDir,`${context.packager.appInfo.productFilename}.app`,'Contents','Resources'):path.join(context.appOutDir,'resources');
  const archive=path.join(resources,'app.asar');
  if(fs.existsSync(archive)){
    auditArchive(listPackage(archive));
  }
  if (context.electronPlatformName !== 'darwin') return;
  const app = path.join(context.appOutDir, `${context.packager.appInfo.productFilename}.app`);
  // These Finder metadata attributes invalidate signing. Only clean generated build output.
  // Keep quarantine and all other security attributes intact.
  for (const attribute of ['com.apple.FinderInfo', 'com.apple.ResourceFork']) {
    const result = spawnSync('/usr/bin/xattr', ['-dr', attribute, app], { encoding: 'utf8' });
    if (result.status !== 0) throw new Error(`Cannot prepare generated app for signing: ${result.stderr || result.error}`);
  }
};
