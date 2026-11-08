## Facts

- F1 — `clearHint` in `src/core/shift.js` builds the CLI sentence from `keepOldSessions` alone: with none kept it says the waiter "then removes it from the session list once Keel's store holds its transcript".
- F2 — `removeOldSessions` refuses `claude rm` for a session whose host-recorded worktree (`~/.claude/jobs/<id>/state.json` `worktreePath`, read by `hostWorktree`) exists and is "in use", through a local `inUse(worktree, row)` with three reasons in order: the hand-off's worktree, a worktree bound to a role, another listed session's cwd. The first two need no host call; the third needs `claude agents`.
- F3 — `ready` knows both inputs of the first two reasons: the session id (`cli.session`) and the hand-off's worktree (`where.worktree`, which `queueHandOff` stores as `entry.worktree`); `roles.json` is in the chat store.
- F4 — The fixture `handover_old_session` in `scripts/validation/shift.py` writes the host's `jobs/<id>/state.json` and the contract fake `claude`, runs `shift ready --wake`, then the real tick, and returns the `rm` calls; it already covers the in-use and the removable case (#492), and discards `ready`'s output.

## Decisions

- D1 — `inUse` moves out of `removeOldSessions` into a function both callers use. `ready` calls it with the hand-off's worktree and the roles, and no `claude agents` listing, so the third reason (another listed session) is not evaluated at `ready`.
- D2 — When the session is in use, `clearHint` replaces the removal clause with: it stays in `claude agents` because its worktree `<path>` is the new shift's (or bound to role `<r>`), `claude rm` would delete that worktree, and opening it again brings it back beside the new shift. The `keep_old_sessions > 0` clause keeps its text and gains the same worktree sentence when in use.
- D3 — The limit is stated: a session kept only because another listed session runs in its worktree is still described as removed by `ready`; `keel shift status` names it afterwards (#492 D3). Evaluating that reason at `ready` would add a `claude agents` call to a command that has none, for a rarer case.
- D4 — The session's host worktree not existing, or the host recording none, is "not in use": the promise of removal stands, as it does in the hand-over.
