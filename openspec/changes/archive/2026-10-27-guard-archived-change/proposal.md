## Why

Issue #491, approved by the owner on 2026-10-27, who chose to let a guard over an archived, completed task stop guarding. In ChipSTRIDE, under Claude Code's auto mode, a change went from `task-start` to archive under the standing `archive` authorization, and the next write, the new change's proposal, was refused because the manifest still pointed at the archived change. `keel guard clear` was the only way out, and the auto-mode permission classifier refused it, so every change after the first in a session needed a person to run `! keel guard clear`.

## What Changes

- **A manifest whose change was archived with its task checked enforces nothing.** When the guarded change's directory is gone, the write guard looks for its archived copy under `openspec/changes/archive/<date>-<change>/`; if that copy's `tasks.md` shows the guarded task checked, the write passes as it would with no manifest.
- **`keel guard status` says so** with the status `archived` and the problem code `task-archived`, names the archived directory and `keel guard clear`, and exits 0.
- **Every other vanished change still fails closed** (#56): a change gone without an archived copy, or archived with the guarded task unchecked, is refused as stale, as before.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-touch-write-guard`

## Impact

`plugins/keel/scripts/pretooluse-guard.js`, `src/core/guard.js`, `bin/keel.js`, `scripts/validation/guard.py`, `scripts/validation/registry.py`, the README in both languages, the published spec, and the changelog.
