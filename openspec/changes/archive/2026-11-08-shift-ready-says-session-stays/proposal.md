## Why

Issue #506, filed 2026-11-08, a bug in the shift feature (bug fixes stay within the 2026-10-14 freeze). The owner asked me to order and work the open issues ("你自己排序继续走", 2026-11-08); this is the smallest step of #506's three expectations, the one that fixes a statement that is false.

`keel shift ready --wake` in a CLI session whose own worktree is the one the new shift starts in — every session that made its worktree with `EnterWorktree` and bound the role to it — prints that "a waiter stops it — then removes it from the session list once Keel's store holds its transcript". The hand-over then does not remove it: `claude rm` deletes the session's worktree, and the worktree is the new shift's (#492 D1, F4), so the session stays in `claude agents`, and opening it later puts two live sessions in one worktree. `keel shift status` says so after the fact (#492 D3); `ready` still promises the opposite. Both inputs, the session's host-recorded worktree and the hand-off's worktree, are known when `ready` runs.

## What Changes

- **`keel shift ready --wake` says the old session will stay** when its host-recorded worktree is the worktree the new shift starts in (or is bound to a role), the same test the hand-over applies before `claude rm`. The hint names that it stays in `claude agents`, the worktree, that `claude rm` would delete it, and `claude attach <id>`, and no longer says it is removed. The `--json` `clear` field carries the same text.
- The test is one function used by both `ready` and the hand-over, so the promise and the action cannot drift apart.
- Unchanged: the promise of removal when nothing keeps the session; the `keep_old_sessions` wording; the hand-over; `keel shift status`.
- Not in this change: telling a woken old session that it was replaced, and refusing its gates (#506 expectation 1); marking the session in the host's list or a `claude rm` that keeps the worktree (expectation 3). #506 stays open for them.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`

## Impact

`src/core/shift.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, the published spec, and the changelog.
