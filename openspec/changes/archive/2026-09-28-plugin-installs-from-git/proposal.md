## Why

The owner wants Keel listed in Anthropic's official plugin directory (`anthropics/claude-plugins-official`), with one release flow feeding npm, Keel's own marketplace, and that directory. On 2026-09-28 every third-party entry in that directory (262 of them) took its plugin from a git repository pinned to a commit, and none from npm. Keel's Claude marketplace entry takes its plugin from the npm package (#164, 5.74.0), and declares the plugin's skills, agent, and hooks inline in the entry itself. The official directory would have to copy those declarations into its own file.

A bundled OpenSpec was considered first and dropped. A probe on Claude Code 2.1.283 installed Keel from a git source pinned to a commit and the host ran the dependency install from the committed `npm-shrinkwrap.json`, so the plugin arrived with OpenSpec 1.13.2 and `keel --doctor` reported `openspec: ok`. The owner decided on 2026-09-28 to go straight to git and not bundle.

## What Changes

- **The plugin's manifest moves to the repository root.** A new `.claude-plugin/plugin.json` declares the canonical skills, the Claude agent, and the hooks, with script paths under `plugins/keel/`. It is the one Claude manifest; any marketplace entry, ours or the official directory's, only has to say where the repository is.
- **Keel's own marketplace installs from git.** The entry's source is `https://github.com/TanglmChris/keel.git` at the release tag `v<version>`, and the entry carries no component declarations. `bump_version.js` moves the tag with every other marker. Our marketplace and the official directory install the same tagged tree.
- **Every release carries its official directory entry.** `scripts/official_entry.js <version> <sha>` prints the entry, pinned to the commit the release tag points at, and the release job appends it to the GitHub release notes. Submitting it, and any later update request, is the owner's act.
- **npm is unchanged.** The same commit is still published as `@christang/keel`, for the terminal and Codex.
- **Codex is unchanged.**

## Non-goals

- Bundling OpenSpec into the repository.
- Submitting to the official directory. The submission form is filled by the owner.
- Changing how OpenSpec is upgraded: the shrinkwrap still pins it, and a release still carries it.

## Capabilities

### Modified Capabilities

- `keel-native-plugin-package`: the Claude plugin is the tagged repository tree, described by a root manifest, and each release states its official directory entry.

## Impact

- `.claude-plugin/plugin.json` (new), `.claude-plugin/marketplace.json`, `scripts/bump_version.js`, `scripts/official_entry.js` (new), `.github/workflows/publish.yml`, `scripts/validate_plugin.py`, `plugins/keel/scripts/session-start.js` and `bin/keel` (comments), `README.md`, `README.zh-CN.md`.
- Installing the Claude plugin now needs `git` and network access to GitHub, and still needs `npm`, which the host runs to install the pinned OpenSpec. That install step is the host's behavior, observed on 2.1.281 (#164) and 2.1.283; Keel does not control it.
- Existing Claude users move from the npm-sourced plugin to the git-sourced one at their next update.
- Between a release PR merging and its tag being created, a marketplace refresh names a tag that does not exist yet; the fetch fails and succeeds on retry. This is the same window the npm pin had.
