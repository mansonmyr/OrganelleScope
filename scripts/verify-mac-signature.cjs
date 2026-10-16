const path = require('node:path');
const { spawnSync } = require('node:child_process');

// A successful packaging command alone does not establish a valid app signature.
module.exports = async function verifyMacSignature(context) {
  if (context.electronPlatformName !== 'darwin') return;
  const app = path.join(context.appOutDir, `${context.packager.appInfo.productFilename}.app`);
  for (const target of [app, path.join(app, 'Contents/Resources/backend/organellescope-backend')]) {
    const result = spawnSync('/usr/bin/codesign', ['--verify', '--deep', '--strict', '--verbose=2', target], { encoding: 'utf8' });
    if (result.status !== 0) throw new Error(`Packaged signature verification failed for ${target}:\n${result.stderr || result.error || 'unknown error'}`);
    console.log(`Verified development signature: ${target}`);
  }
};
