## Why

Issue #300 (2026-10-12): a Claude desktop scheduled task starts its runs in the folder of the session that created it. rtl_ppa_prj's patrol task, created by the coordinator, therefore ran in the coordinator's worktree, and Keel's chat hooks treated each run as `iecc-pm`: its SessionStart wrote the coordinator's `session_started`, which would fire a pending `keel shift ready --wake` early, and its SessionEnd marked the coordinator offline while its session was alive. The owner decided on 2026-10-12 to recognize such a run in the hooks and to settle the wake.

## What Changes

- The chat SessionStart hook keeps, per host session id, the role's presence as it was before. A first UserPromptSubmit whose prompt starts with `<scheduled-task` marks that session a host run and restores the presence. After that, the session's hooks touch no presence, inject no chat notice, wake nothing, and its SessionEnd changes nothing.
- The `keel shift ready --wake` waiter fires only once a qualifying start has stayed unchanged for a settle time (15 s, `KEEL_SHIFT_WAKE_SETTLE_MS`).
- `keel patrol task` says to create the task from a folder bound to no role.

## Capabilities

### Modified Capabilities
- `keel-cross-host-mailbox`: a host-run session does not act as the worktree's role.
- `keel-shift-change`: the wake settles before it fires.

## Impact

`src/core/chat/notice.js`, `src/core/shift.js`, `src/core/patrol.js`, `docs/shift-change.md`, `README.md`, `scripts/validate_plugin.py`, the published specs, and the changelog.
