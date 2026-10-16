# Mac development packaging repair — 16 October 2026

The installed 0.1.1 app at `/Applications/OrganelleScope.app` failed `codesign --verify --deep --strict` with “code has no resources but signature indicates they must be present.” Its main executable had an Electron linker signature, no bound Info.plist and no sealed resources. The earlier packaging workflow completed with code signing skipped; that successful build did not establish that the resulting installed app passed macOS integrity verification.

Version 0.1.2 explicitly requests an ad-hoc development signature, includes the backend executable in the signing inputs, and verifies the final app and backend with strict codesign checks. The build fails on verification failure. Hardened runtime remains enabled; development entitlements permit Electron JIT execution and loading libraries without a common Apple Team ID. These are development signing settings, not a production Apple identity.

Local FinderInfo/ResourceFork metadata can itself prevent signing. A macOS-only afterPack hook removes those two attributes from generated app output before signing. It does not clear quarantine or change system security settings.

For installation, use the rebuilt DMG, copy the app into Applications and choose Replace. If macOS then displays an unidentified-developer/not-notarized warning, the user must decide whether to allow this specific app using Apple's documented Privacy & Security → Open Anyway flow. A developer-signature check does not confer Apple trust or notarization. Do not disable Gatekeeper system-wide. Retain a copy of any failing installer for diagnosis rather than assuming every damaged-app warning is harmless.

References: [Apple app safety and opening guidance](https://support.apple.com/en-us/102445), [electron-builder Mac signing options](https://www.electron.build/v26/docs/mac/).

Local file-provider-managed Documents storage reattached empty FinderInfo metadata after cleanup during diagnosis. The local packaging wrapper now builds .app bundles in temporary storage outside that tree and copies only finished DMGs to release/. CI workspaces are not affected by this local Documents behavior.

Local verification: the replacement app and bundled backend pass strict codesign verification; the DMG passes hdiutil integrity verification. The packaged app opens its actual app.asar UI and starts the bundled backend without an external Python environment. The local installer is release/OrganelleScope-0.1.2-arm64.dmg, with a sibling SHA-256 file. These checks do not assert that Gatekeeper will accept an internet download without an explicit user exception.
