# Building and publishing

Use Node.js 24 and an isolated Python environment (CI uses Python 3.12). The [manual](../MANUAL.md#57-development-setup) describes source setup. Run backend tests, frontend tests and the UI production build before packaging.

Native builds require `backend[test]` and PyInstaller. `npm run package` builds the UI, freezes the backend, collects dependency notices and builds the host platform installer. Output goes to the ignored `release/` directory. Windows targets x64; macOS targets Apple Silicon. Cross-platform packaging is performed on native GitHub-hosted runners.

## Dependency notices

`scripts/dependency-notices.py` runs after freezing, with the same Python environment. It collects licence texts for declared runtime requirements, providers found in the actual PyInstaller module graph and their dependencies. Frontend production dependency notices are collected separately. These build-specific files live in ignored `build/notices/`, are included at `Resources/notices` (macOS) or `resources/notices` (Windows), and are attached to the build artifact. Electron retains its bundled Chromium notices. Required predecessor/model licences remain in `third_party/`; retired model licences are preserved in Git history rather than redistributed as current components.

## Release process

1. Commit a consistent application/backend version and release notes. Keep user data, credentials, models and local sample reports out of Git.
2. Push the tested source to the default branch, then push its version tag, for example `v0.2.5-rc.1`.
3. The installer workflow runs source tests, freezes and smoke-tests both backends, generates notices and packages both platforms. macOS additionally verifies the mounted installer.
4. After both jobs succeed, the publish job downloads their artifacts, checks their exact SHA-256 hashes and creates a draft GitHub Release. It uploads both installers, checksums, notices and verification records before publishing the prerelease. Failed uploads leave a draft rather than a partly published release. Manual workflow runs build artifacts only.
5. Check the release assets and installation behaviour. Record issues against the exact version and checksum. No workflow claims biological validation.

The compact installers contain the analysis application, not the approximately 6.98 GB optional Gemma weights/runtime. Image analysis works without the assistant. Model setup is separate and documented in [Local assistant](LOCAL_ASSISTANT.md). macOS is ad-hoc signed and not notarized; Windows lacks a publisher certificate. These release candidates are evaluation builds.

Desktop downloads use [GitHub Releases](https://github.com/mansonmyr/OrganelleScope/releases), rather than the package/container registries in GitHub Packages. No publishing token is stored in the repository: only the publish job receives the workflow's temporary contents-write token.
