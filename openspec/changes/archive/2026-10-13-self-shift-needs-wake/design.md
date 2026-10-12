## Context

Issue #317 and the owner's decision of 2026-10-13 recorded on it. Not chosen: binding a role automatically from the worktree name (it invents roles a coordinator did not plan); a wake keyed by worktree instead of role (a second presence and delivery channel). Out of scope: a bound role with no request running `ready` without `--wake`, which keeps its current hint.

## Facts

- F1 — `ready --wake` with no chat role is refused (`src/core/shift.js` `ready`), and the wake is a chat record addressed to a role.
- F2 — `readyRole` already refuses an unbound worktree while any role's shift request is open, so an unbound `ready` that reaches the note is never answering a request.
- F3 — The owner's remark of 2026-10-05 that a shift change needs no chat role is what `shift-without-role` checks; a coordinator may still tell an unbound session by other means.

## Decisions

- D1 — In a worktree with no chat role and no `--role`, `keel shift ready` without `--force-reason` is refused before the readiness check and stores nothing: `This worktree has no chat role, so nothing will start the session that follows a clear: no request can name it, and --wake needs a role. Bind one with \`keel chat role --set <name>\` and run \`keel shift ready --wake\`, or give --force-reason "<who starts the new session>".`
- D2 — With `--force-reason`, the unbound note's head carries `Started by hand: <reason>.`, and the clear hint reads `Without a chat role nothing wakes the new session; <reason> — tell it to run \`keel shift resume\`.`
- D3 — `docs/shift-change.md` and `docs/shift-change.zh-CN.md` say that an unbound self-shift needs a role and `--wake`, or `--force-reason` naming who starts the new session; both keep saying a chat role is optional for a coordinator-driven change.
