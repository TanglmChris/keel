## Why

rtl_ppa_prj's whole-team shift change on 2026-10-12 hit three gaps (reported by iecc-pm):
- #289: the coordinator cleared itself before anyone started the roles whose notes waited; with no waker on Claude, the whole team sat idle for 6 h 42 min, and the coordinator's session-level schedules died with it.
- #290: roles whose sessions worked outside their bound worktree ran `ready` there; the notes landed under the worktrees, the roles' requests stayed "not ready", and the coordinator had to match notes to roles by hand.
- #291: `keel shift status` suggested `keel shift start worktree <name>` for a worktree note, which cannot parse.

Owner decisions, 2026-10-12: start the others before clearing yourself; `ready --role` with the misfiling refused; and fix the hint.

## What Changes

- `keel shift check`, for a role that requested shift changes, reports each role whose note waits and that this role has not started since, so `ready` refuses until they are started (or `--force-reason`). A new coordinator's `keel shift resume` lists the roles still waiting for `start`. The request text and the `ready` output name host-session state a clear destroys — scheduled jobs, Remote Control — as something the note should carry.
- `keel shift ready --role <role>` files the note under that role when it has an open request and this worktree is bound to no other role. `ready` in a worktree with no chat role while role requests are open is refused, naming `--role` for each.
- `keel shift status` shows, for a role still requested, any worktree note written since; for a worktree note it says to run `keel shift resume` in that worktree, naming its path.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the coordinator's own shift, notes filed by role from another worktree, and accurate status hints.

## Impact

`src/core/shift.js`, `docs/shift-change.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
