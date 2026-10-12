## Why

Issue #317 (2026-10-13): the Keel maintenance session changed its own shift from a worktree bound to no chat role. `--wake` is refused there, plain `keel shift ready` accepted the note and closed with a hint to tell the new session to run `keel shift resume`, and the session cleared. Nothing woke the cleared session; the owner had to open a new one by hand. No request can name an unbound worktree, so `ready` there is always a self-shift, and without `--wake` a self-shift that clears has nobody to start the next session. Owner decision, 2026-10-13: refuse it and point the way.

## What Changes

- `keel shift ready` without `--role`, in a worktree bound to no chat role, is refused, naming `keel chat role --set <name>` followed by `keel shift ready --wake`, unless `--force-reason "<who starts the new session>"` is given.
- A note filed that way records the reason as who starts the new session, and the clear hint names it.
- `docs/shift-change.md` and its Chinese translation stop saying a shift change needs nothing but the repository.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: `ready` in an unbound worktree requires a role and `--wake`, or a stated reason.

## Impact

`src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
