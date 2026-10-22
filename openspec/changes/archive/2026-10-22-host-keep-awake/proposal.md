## Why

Issue #447, approved by the owner on 2026-10-21 under the shift freeze. The spec currently prescribes the workaround, so the requirement changes too.

`keel shift check` lists the `caffeinate -i -t 300` that Claude Code runs under the session as work left running in the worktree. Every CLI shift therefore needs `--force-reason`, and every CLI note carries a "Left as is" block about the keep-awake. All 5 CLI-era keel-maint notes have one. When forcing becomes routine, a real process left running is easier to force past without a look.

## What Changes

- **The host's keep-awake is not a loose end.** `keel shift check` no longer lists a `caffeinate` whose parent is an ancestor of the checking process, which is the session's own host process. Any other process in the worktree is still listed. That includes a `caffeinate` started anywhere else, and any other program.
- **`/keel:shift` and the docs stop prescribing `--force-reason` for it.**

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`

## Impact

`src/core/shift.js`, `plugins/keel/commands/shift.md`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, the published spec, and the changelog.
