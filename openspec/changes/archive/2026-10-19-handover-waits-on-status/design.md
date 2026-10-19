## Context

#388 added a wait for a session blocked on a question, on a premise nobody measured. #393 measured it.

## Facts

- F1 — A background session blocked on `AskUserQuestion` reads `{"status": "waiting", "waitingFor": "input needed", "state": "blocked"}` in `claude agents --json --all` (throwaway session, Claude Code 2.1.303, 2026-10-19).
- F2 — A session whose turn has ended reads `status: idle`; its `state` is the host's label of its last message and stayed `working` after keel-maint's final reply (`~/.claude/jobs/b4d145a2*/timeline.jsonl`).
- F3 — A stopped session has `state: stopped` and no `status`.

## Decisions

- D1 — `finished(row)`: true when the row is absent, has no `status`, or has `status: idle`; false otherwise. `state` is not read. An unknown future status waits, so the patrol's 15-minute pending risk reports it rather than a session being cut off.
