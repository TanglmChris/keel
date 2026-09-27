## Why

Issue #164. On Claude Code a Keel release arrives in two parts that are versioned separately and updated separately:
- the `keel` CLI, updated with `npm i -g`;
- the plugin, updated with `claude plugin marketplace update` followed by `claude plugin update`.

The version-drift line then tells the user to restart. On 2026-09-27 a restart after the 5.73.1 release still showed plugin 5.72.0, CLI 5.72.0, protocol 5.73.1. It took three commands and a second restart to line them up. The owner asked for updates the user does not notice. On 2026-09-27 they chose what that means: a release goes live silently at the next launch, or earlier via `/reload-plugins`, and the only human act left is committing a refreshed protocol block.

The probes recorded on #164 found three host facts that make this possible on Claude Code 2.1.281:
- `/reload-plugins` swaps plugin hooks in a running session.
- A plugin's `bin/` directory is on the Bash tool's PATH.
- A marketplace entry can take its plugin from an npm package, and the entry itself acts as the manifest.

What still keeps the user in the loop is Keel's own shape: its plugin is a copy of `plugins/keel` and nothing more, so the CLI has to arrive through a second channel.

## What Changes

- **The Claude plugin is the published npm package.** The Claude marketplace entry takes the plugin from `@christang/keel`, pinned to the same exact version as the entry. The entry is the plugin's manifest and declares the skills, the Claude agent, and the hooks inside `plugins/keel`. The npm publish the land job already performs becomes the plugin release. Plugin and CLI are one artifact on Claude.
- **The package runs as a plugin.** It gains:
  - an extensionless `bin/keel`, so a bare `keel` resolves from the plugin's `bin/`;
  - `npm-shrinkwrap.json` in place of `package-lock.json`, so the host can install the pinned OpenSpec dependency. npm never publishes `package-lock.json`.
- **Doctor reads the lockfile npm reads.** When looking for the version a repository declares, doctor tries `npm-shrinkwrap.json` first and falls back to `package-lock.json`. This is the precedence npm itself applies, and it keeps doctor correct on this repository after the rename.
- **The hook runs the CLI it shipped with.** Inside the package, the SessionStart hook runs its own `bin/keel.js` in preference to whatever `keel` is on PATH. `KEEL_CLI` still overrides both. The hook also compares the `keel` on PATH against its own. The host puts the user's PATH ahead of plugin directories, so a stale global install shadows the plugin's copy for every command the agent runs. The hook reports that and names both remedies.
- **The drift line names the reload.** It stops saying an update applies only after restarting. It says hooks are fixed when the plugin loads, and that an update applies after `/reload-plugins` or at the next session start.
- **Codex is unchanged.** `plugins/keel` keeps its Codex manifest, its default-discovered hooks, and its dependence on a separately installed CLI.

## Capabilities

### Modified Capabilities

- `keel-native-plugin-package`: the Claude marketplace installs the published package, which carries its own CLI; the separately installed CLI stays a prerequisite on Codex only.
- `keel-native-runtime-projection`: version drift names `/reload-plugins`, and the hook reports a `keel` on PATH that disagrees with the plugin's own.

## Impact

- `.claude-plugin/marketplace.json`, `bin/keel` (new), `package-lock.json` → `npm-shrinkwrap.json`, `bin/keel.js` (the doctor lockfile read), `plugins/keel/scripts/session-start.js`, `scripts/bump_version.js`, `scripts/validate_plugin.py`, `README.md`, `README.zh-CN.md`.
- Existing Claude users move to the npm-sourced plugin on their next marketplace refresh and plugin update. Anyone who also keeps a global `keel` will see it reported whenever its version differs from the plugin's. Codex users see no change.
- For the few minutes between a release PR merging and its npm publish, a marketplace refresh names a version the registry does not have yet. The pinned fetch fails and succeeds on retry. Without the pin, the previous package could be cached under the new label.
- Out of scope, and next on #164: declaring auto-update for the marketplace from `keel --init`, and a standing authorization for the agent to refresh the managed protocol block.
