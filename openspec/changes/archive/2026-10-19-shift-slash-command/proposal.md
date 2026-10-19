## Why

Issue #386: the owner asked on 2026-10-19 for a session's own shift change to be one slash command. Today a session has to remember the order — `keel shift check`, the note, `keel shift ready --wake`, then the host's own steps — and what each outcome of the check means. On 2026-10-19 the check's only item was the host's own `caffeinate -i -t 300`, started under the Claude process itself, and nothing told the session that this is not a loose end. The shift feature is frozen; the owner was told the cost (one command file, one scenario, one minor version) and agreed to make this the exception.

## What Changes

- The Claude plugin ships `/keel:shift`: it has the session run `keel shift check`, settle each item (and tell a host keep-awake process from a loose end of its own), write the hand-off note, and run `keel shift ready --wake --file -`, then follow what that prints for the host.
- The root `.claude-plugin/plugin.json` declares the command. Codex has no plugin commands, so its manifest is unchanged.
- The shift mechanism itself does not change.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: a session can change its own shift with one slash command.
- `keel-native-plugin-package`: the Claude manifest declares the command.

## Impact

`plugins/keel/commands/shift.md`, `.claude-plugin/plugin.json`, `scripts/validate_plugin.py`, `docs/shift-change.md` and its zh-CN twin, two published specs, the changelog.
