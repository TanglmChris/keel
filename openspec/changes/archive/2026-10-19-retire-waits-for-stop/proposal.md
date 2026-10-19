## Why

Issue #395, the owner's end-to-end test of 5.165.0 on 2026-10-19: the CLI hand-over was delivered in 40 s, but retiring the old session left a running copy of it under the role's name, and the old session kept its name. `retire()` resumes the session for the `/rename` right after `claude stop`, which returns before the process has exited; the host then finds the session still running and starts a copy (reproduced with a throwaway session).

## What Changes

- After `claude stop`, the hand-over waits until `claude agents` shows the old session stopped or gone, bounded, before resuming it for the rename. A session that never shows as stopped is not resumed; its rename is recorded as not shown and the hand-over goes on.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: the CLI hand-over resumes the old session for its rename only once it has stopped.

## Impact

`src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md` and its zh-CN twin, one published spec, the changelog.
