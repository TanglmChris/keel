## Why

Issue #337 (rtl_ppa_prj, 2026-10-14): the owner wants the Claude plugin to update from npm, the package the `keel` CLI already comes from. Today the plugin is cloned from GitHub at the release tag, and on 2026-10-14 a marketplace refresh failed on an SSH host key while npm already had the release, so the plugin and the CLI stood one version apart.

The issue asks for a marketplace manifest inside the npm package, for an npm marketplace source. Claude Code does not implement one: its marketplace reference lists the `npm` marketplace source as `Fails to load: NPM marketplace sources not yet implemented`, and the installed 2.1.302 binary carries that string. An npm **plugin** source is implemented. The owner chose (2026-10-18), knowing 5.80.0 had moved the plugin from npm to git, to take the plugin from npm again: the 5.80.0 reasons no longer bind — the components live in the root manifest, and Anthropic's directory tracks its own `claude-directory` branch.

## What Changes

- Keel's Claude marketplace entry takes the plugin from npm: `{"source": "npm", "package": "@christang/keel", "version": "<release version>"}`. `bump_version.js` moves that version with the others.
- The npm package ships `.claude-plugin/plugin.json`, so the package root is the plugin. Measured: the published 5.140.0 package installed through an npm entry has `Skills (0)` and `Hooks (0)`.
- The install smoke installs what `npm pack` produces, served to the host through a scratch git repository, since an npm source refuses a local folder or `file:` path.
- README: the plugin comes from the npm package; the marketplace catalog itself is still read from GitHub, and can be read over HTTPS with a `url` marketplace source instead of a git clone.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`: the Claude catalog names the npm package; the Claude plugin is the npm package.

## Impact

`.claude-plugin/marketplace.json`, `package.json`, `scripts/bump_version.js`, `scripts/validate_plugin.py`, `README.md`, `README.zh-CN.md`, one published spec, the changelog.
