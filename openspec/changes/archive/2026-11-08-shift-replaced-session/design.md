## Facts

- F1 — The hand-over queue holds one JSON per role at `shift/queue/<role>.json`: `role`, `session` (the old session's full id), `pid`, `worktree`, `state` (`pending`, `starting`, `failed`, `delivered`), and once delivered `delivered_at`, `new_session` (eight characters) and `new_name`. `handOffs(where)` reads them all.
- F2 — A Claude Code CLI session's id is in `CLAUDE_CODE_SESSION_ID` for the commands it runs, and in `session_id` of every hook payload. `cliSession()` already reads the former for `shift ready`.
- F3 — The chat hook (`hook()` in `src/core/chat/notice.js`, run by `mail-hook.js` for `SessionStart` and `UserPromptSubmit`) already locates the worktree's chat store and role and builds the additional context for both events; `twinWarning` already warns, in `keel context`, when two live sessions are bound to a role.
- F4 — `runGate` dispatches the three stages and `taskStart` is the only one that arms a guard; `gateResult` and `problem` build a refusal that `renderGate` prints.

## Decisions

- D1 — `replacedBy(where, sessionId)` in `shift.js` returns `{ role, newSession, deliveredAt }` when some hand-over of this repository's store is `delivered`, has `session === sessionId` and a `new_session`, and `sessionId` does not start with that `new_session`; otherwise null. A missing id gives null. It reads only the queue (F1) and no process or host (owner, 2026-11-08).
- D2 — `replacedNotice(info)` is one sentence shared by all three surfaces: the role, the delivery time, the new session id, "this session no longer owns the role and shares its worktree with the new shift", and "tell the user before doing anything here; to use this session again the user must end the new shift first".
- D3 — The chat hook prepends the notice to the context it returns on `session-start` and `user-prompt-submit`, using the payload's `session_id`, else `CLAUDE_CODE_SESSION_ID`. A hook failure to read the queue says nothing, as the rest of the hook does.
- D4 — `runGate` checks `replacedBy` for the stage `task-start` before selecting anything and returns `fail` with problem code `session-replaced` and the notice; it writes no guard and records no anchor. `ready` throws `ShiftError` with the notice before it queues. `task-complete` and `change-close` are not refused: finishing and closing what was started stays possible.
- D5 — Only the latest hand-over of a role is consulted (F1). A session two shifts back is normally gone with `claude rm`; one that was kept is not announced, and that is a stated limit, not a defect to chase.
- D6 — No escape hatch is added (the shift feature is frozen, memory `shift-feature-is-frozen`): a user who wants the old session back ends the new shift, and a later hand-over from the new session replaces the entry.
