## Context

The owner's decisions of 2026-10-19: CLI self-shift = stop the old, start a new one, keep the old findable; one model-free waker. Measured that day: `claude agents --json` reports `status` `idle`/`busy` for running sessions; `claude stop` keeps the conversation; `claude --bg` in a trusted worktree starts a new session; a never-trusted directory refuses with "Workspace not trusted".

## Facts

- F1 — `ready --wake` (`src/core/shift.js`) records the desktop session and process and arms a detached `wake-wait` waiter that needs a clear.
- F2 — The CLI session's environment carries `CLAUDE_CODE_ENTRYPOINT=cli`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_PID`.
- F3 — `keel tick` (5.155.0) is the model-free step the owner's launchd job runs; since 5.156.0 it also resumes ended CLI roles.

## Decisions

- D1 — In a CLI session `ready --wake` writes `CLI session: <id>.` and `CLI process: <pid>.` into the note, writes `<chat store>/shift/queue/<role>.json` = `{ role, session, pid, worktree, requested_at, state: "pending" }`, arms no waiter, and its output says to end the turn now and that `keel tick` stops this session once idle and starts the next.
- D2 — `keel tick` handles each `pending` entry: it reads `claude agents --json`; a row with the entry's `sessionId` and status `busy` waits; otherwise (idle, or no such row) it runs `claude stop <row.id>` when the row exists — the 8-character job id; `stop`, `attach` and `logs` refuse the full session id (`No job matching`, measured 2026-10-19), while `--resume` takes the full id, then `claude --bg -n <role> --permission-mode <mode> "<role>: your new shift starts now. Run keel context, then keel shift resume."` in the entry's worktree. Exit 0 records `state: delivered`, `delivered_at` and `new_session` (from `backgrounded · <id>`); otherwise `state: failed` and `error` (last stderr line). Entries are handled once.
- D3 — `keel shift status` prints a `Hand-offs:` section, one line per entry: role, state, times, the new session, the error, and `claude attach <job id>` (the old session's first 8 characters, as `claude agents` prints it) to reopen the old one.
- D4 — `keel patrol` adds a risk for an entry that `failed` or has been `pending` for over 15 minutes: `<role>'s CLI hand-off <state> …`.
- D5 — `shift: permission_mode:` (one of `default`, `acceptEdits`, `auto`, `plan`, `bypassPermissions`) sets the mode; default `auto`; any other value is ignored by name.
- D6 — The desktop clear path is unchanged for desktop sessions; this team no longer runs it, so #346 is closed as not applicable rather than fixed.
