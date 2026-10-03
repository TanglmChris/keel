## Why

Issue #175. On 2026-10-03 the owner started Keel's submission to Anthropic's plugin directory. The submission flow has moved to the claude.ai developer portal (`claude.ai/directory/manage`), and a plugin bundle there tracks a branch of a GitHub repository rather than a pinned commit.

Validating `TanglmChris/keel` passed, but with holds:
- The name `keel` belongs to an existing directory connector, and only its owner can publish under it. It is also close to `deel`, `keni`, `kernel`, and a plugin `hancks/keel`.
- The listing was the whole repository, 1,266 files and 7.1 MB. Only the first 512 files were scanned, and `keel/CHANGELOG.md` exceeds 256 KiB.
- There was no icon. The portal takes the icon only on the first save or submit.

The owner chose the name `keel-openspec` for the directory only. The repository name, the npm package `@christang/keel`, and the `keel@keel-marketplace` installs stay as they are. The owner also chose a dedicated branch that each release regenerates, over a second plugin copy kept in `main`.

## What Changes

- **A directory tree built from the npm package.** `scripts/directory_tree.js <dir>` writes the files `npm pack` would publish: about 65 files that already form a complete Claude plugin carrying its own CLI. It adds `.claude-plugin/plugin.json` with the name `keel-openspec` and `.claude-plugin/icon.png`, the Keel mark at 1024×1024. The root manifest in `main` keeps the name `keel`.
- **Each release updates the `claude-directory` branch.** `scripts/directory_branch.js <version> <sha>` commits that tree as the next commit of `claude-directory` and pushes it. The release job runs it after tagging, and the release notes name the branch commit. The sha-pinned "Official directory entry" and `scripts/official_entry.js` are removed, because the directory no longer takes a pin.
- **The icon** lives at `assets/directory/icon.png`, drawn from the same block mark the SessionStart panel uses.
- **Documentation**: the README paragraph about the directory entry describes the branch.

## Capabilities

### Modified Capabilities

- `keel-native-plugin-package`: "Each release states its official directory entry" is removed, and "Each release updates the directory branch" is added.

## Impact

- New: `scripts/directory_tree.js`, `scripts/directory_branch.js`, `assets/directory/icon.png`.
- Removed: `scripts/official_entry.js`.
- Changed: `.github/workflows/publish.yml`, `scripts/validate_plugin.py`, `README.md`, `README.zh-CN.md`, `keel/CHANGELOG.md`.
- The npm package gains the 8.7 KB icon under `assets/`. Nothing else changes for npm or marketplace users.
- The submission itself is made by the owner's confirmation, after the first release creates the branch.
