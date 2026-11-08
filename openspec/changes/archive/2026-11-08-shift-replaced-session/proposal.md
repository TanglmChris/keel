## Why

Issue #506, expectation 1, reported from a Windows project on 2026-11-08 (Keel 5.216.0, Claude Code 2.1.319). After `keel shift ready --wake` in a worktree the session made itself with `EnterWorktree`, the old session stays in `claude agents` because `claude rm` would delete the worktree; a message from the user woke it, and two live sessions shared one worktree. Nothing told the old session it had been replaced, and nothing stopped it from starting a task or handing over again. Expectation 2 shipped in 5.218.0; this is expectation 1, scoped by the owner on 2026-11-08 to "a notice, and refusing the commands that begin new work" (not a write block).

## What Changes

- **A replaced session is told, first.** The chat hook that already runs on `SessionStart` and `UserPromptSubmit` puts a line at the front of what it injects when the session is the old session of a `delivered` hand-over: it names the role, the time, and the new session, says the session no longer owns the role and shares its worktree with the new shift, and tells it to say so to the user before doing anything in that worktree.
- **`keel gate task-start` and `keel shift ready` refuse it,** pointing at the new session: `task-start` returns `fail` with a problem naming the hand-over and writes no guard or anchor; `ready` exits non-zero with the same words and queues nothing.
- **Judged by the hand-over record alone.** A session is replaced when the role's queue entry is `delivered`, names it as the old session, and names a new one. Keel does not probe whether the new session is still alive, so the hook stays cheap; the notice says what the record says. Only the role's latest hand-over is consulted, because the queue keeps one entry per role.
- **Everything else is unchanged:** reading, chatting, `keel shift status` and writing files are not blocked, and no session id, no `CLAUDE_CODE_SESSION_ID`, or the new session itself is never treated as replaced.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`

## Impact

`src/core/shift.js`, `src/core/gates.js`, `src/core/chat/notice.js`, `scripts/validation/shift.py` and `registry.py`, `docs/shift-change.md` and its Chinese copy, the published spec, and the changelog.
