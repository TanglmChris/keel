## Why

Issue #301 (2026-10-12): in rtl_ppa_prj, `rtl-report` was bound to a worktree no session ran in while its session ran in an unbound one, and `iecc-design-sub` was bound to a removed worktree and an empty one while its session ran in the main checkout. Messages to those roles woke nobody, `rtl-report`'s shift note waited unseen, and nothing in Keel said so. The owner decided on 2026-10-12: report the drift where it is read, and add an explicit cleanup.

## What Changes

- Keel computes binding drift. A *removed binding* is a role bound to a worktree that no longer exists. An *unattended role* is one with something waiting — addressed unread records or a shift note — and no session active for two hours.
- `keel patrol` and `keel --doctor` report the drift; `keel patrol --since-last` reports it when it changes.
- `keel chat role --prune` removes the bindings to removed worktrees and names them.
- A session starting in a worktree with no role, the main checkout included, is told which roles are unattended, so a session that is one of them binds where it runs.

## Capabilities

### Modified Capabilities
- `keel-cross-host-mailbox`: binding drift is reported and removed bindings can be pruned.

## Impact

`src/core/chat/drift.js` (new), `src/core/chat/store.js`, `src/core/chat/cli.js`, `src/core/patrol.js`, `src/core/context.js`, `plugins/keel/scripts/session-start.js`, `bin/keel.js` (doctor), `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
