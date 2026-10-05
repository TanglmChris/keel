## Context

The owner's remark of 2026-10-05: decouple the shift change from chat roles, since Keel may be used where no bot or chat is set up.

## Facts

- F1 — In 5.98.0, `ready` and `resume` call `store.requireRole` and refuse without a role (`src/core/shift.js`).
- F2 — In 5.98.0, the waiting-note line comes from the chat SessionStart hook (`src/core/chat/notice.js`), which says nothing in a worktree without a role. Codex runs no chat hook.
- F3 — `plugins/keel/scripts/session-start.js` renders `keel context --json` on every SessionStart, on Claude and on Codex.

## Decisions

- D1 — A note is keyed by the role when the worktree has one, and otherwise by the worktree: `shift/worktree/<basename>-<first 8 hex of sha256(realpath)>.md`. `resume` and the pointer look for the role's note first, then the worktree's.
- D2 — `request`, `start`, the closing reply, and the on-shift message stay chat records. Without a role, `ready` closes nothing and `resume` posts nothing. Both say so in their output instead of refusing.
- D3 — `keel context` reports a waiting note as one informational line, and its JSON carries `shift`. It does not affect status, selection, or next action, so continuity stays inferred from OpenSpec and Git (keel-stateless-continuity). The SessionStart projection repeats the line. The chat hook's own line is removed, because it would duplicate the projection's line for role-bound sessions.
