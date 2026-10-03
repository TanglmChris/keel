## Why

Issue #204. A Keel release reaches a machine as three separately updated pieces: the global CLI, the Claude plugin, and the Codex plugin. Each project also carries its own protocol block and overlays. On 2026-10-03 the owner had to update each one by hand. The Codex plugin had been stuck at 5.85.0 for days, because its marketplace pointed at a local checkout sitting on a feature branch. Every running session also kept the version it had loaded.

Probes recorded on #204 settled what each host does:
- Codex resolves the plugin root again at every hook call. After `codex plugin add` installs a new version, a running session's next hook runs the new version, even though Codex deleted the old directory. Trust survives an unchanged hook definition.
- Claude binds hooks to the version directory it loaded. It keeps old directories, and `/clear` re-runs the old hook (#172).

The owner decided three things on 2026-10-03:
- One command the owner runs updates everything machine-level.
- Project files are brought forward by each project's own next session, through the existing `protocol-refresh` rule.
- Running sessions adopt the new version automatically, except that the write guard waits for an active task to end.

## What Changes

- **`keel --update` updates every installed Keel component.** After the global CLI, it updates the Claude plugin and the Codex plugin through each host's own commands, when that host is present and has Keel installed. A Codex marketplace that is a local path is reported as needing a manual step, never re-pointed. Each component gets one status line:
  - its old and new version;
  - when the update takes effect;
  - anything the owner must still do.
- **Running Claude sessions adopt an installed update at their next hook call.** Each Claude hook script first checks the host's install record. When it names a newer installed version of this plugin with the same major version, the script hands the event to that version's copy of the same script.
  - The write guard does not hand off while a task's guard manifest is active. The loaded guard keeps enforcing until the task ends.
  - When the hand-off cannot happen, the loaded script runs as before.
- **The session projection stays quiet about an adopted update.** It speaks only when something still needs `/reload-plugins`: changed skills, changed agents, or changed hook declarations.
- **The runtime-management requirement is narrowed.** Hooks and projections still never install or update anything. The owner-run `keel --update` may, through the hosts' own commands.
- **A protocol refresh brings every installed target's overlays forward**, not only the selected target's. Doctor reports an overlay whose version marker differs from the CLI as stale.
- **Documentation**: a capability matrix per host, with the probe evidence, and the update steps in both READMEs.

## Capabilities

### Modified Capabilities

- `keel-native-plugin-package`: `keel --update` coordinates the installed plugins.
- `keel-native-runtime-projection`: Claude hooks hand off to the installed update; the guard defers during an active task; an adopted update is silent unless a reload is needed; the runtime-management requirement is narrowed to hooks and projections.
- `keel-openspec-surface-overlay`: a protocol refresh covers every repository-installed target, and doctor reports stale overlay versions.

## Impact

- New `plugins/keel/scripts/forward.js`.
- Changed: `plugins/keel/scripts/{session-start,mail-hook,pretooluse-guard}.js`, `bin/keel.js`, `scripts/validate_plugin.py`, `scripts/validate_codex_receiving.py`, `README.md`, `README.zh-CN.md`, a new `docs/updating.md`, and `keel/CHANGELOG.md`.
- No new dependency. Hook command strings do not change, so Codex hook trust is kept.
- Hand-off works only from a version that contains it. The first release carrying it can be adopted *from* only by the release after it.
