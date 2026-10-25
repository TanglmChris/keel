## Why

Issue #476, approved by the owner on 2026-10-26. From 00:15 to 07:15 that night the keel-maint tick patrol sent its coordinator the same risk every 30 minutes, 15 times: keel-maint-2's CLI session ran in a directory the 10-25 workspace rename removed. Nothing changed between runs, and every message woke the coordinator. Three gaps were behind it:

- `keel patrol --since-last --notify` sends the hand-off and moved-session risks on every run. They bypass the snapshot that limits the checkout and disk risks to the run where they turn bad.
- Parking the role would not have stopped it: the moved-session risk ignores the park, although `keel chat role` says a parked role is not reported by the patrol.
- Unbinding the role, the owner's choice, needed a hand edit of `roles.json`. Its worktree still existed, and `--prune` only drops bindings to removed worktrees.

## What Changes

- **Standing risks are sent once.** Under `--since-last`, the patrol records the text of each hand-off and moved-session risk in its snapshot. A risk is sent only when its text was not in the previous run's snapshot: when it first appears, when it changes, or when it comes back after clearing. A risk that persists is still printed on every run, marked as already sent. A run without `--since-last` reports every risk, as now.
- **A parked role's moved session is not reported.** The patrol and `keel shift status` skip a parked role's session whose directory is gone.
- **`keel chat role --unset`** removes the calling worktree's binding (`--repo` names another worktree) and says which role it unbound.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`
- `keel-cross-host-mailbox`

## Impact

`src/core/patrol.js`, `src/core/chat/notice.js`, `src/core/chat/cli.js`, `scripts/validation/chat.py`, `scripts/validation/registry.py`, the README in both languages, the published specs, and the changelog.
