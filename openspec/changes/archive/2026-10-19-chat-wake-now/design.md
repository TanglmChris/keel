## Context

The owner's CLI waker (2026-10-19) folds #348 into `keel tick`. The protocol rule that Keel starts no session except through an owner-installed waker (`keel chat wake add`, Codex only) is widened to the two places the owner chose: the launchd job the owner installs from `keel tick task`, and an explicit `keel chat wake now`. Both only resume the role's own recorded session; neither starts a new one.

## Facts

- F1 — In a background CLI session the environment carries `CLAUDE_CODE_ENTRYPOINT=cli`, `CLAUDE_CODE_SESSION_ID` and `CLAUDE_PID` (read 2026-10-19).
- F2 — An idle background session is woken by the chat FileChanged hook within seconds; a stopped one is resumed by `claude --bg --resume <id> "<prompt>"`; adding `-n`, `--permission-mode` or `--model` starts a copy with a new id (measured 2026-10-19).
- F3 — `notice.asleep` and the post output already handle a desktop session with no running process (#331).

## Decisions

- D1 — Presence gains `cli_session`, `cli_pid` and `cli_worktree`, written when `CLAUDE_CODE_ENTRYPOINT` is `cli` and a session id is known, cleared otherwise, and kept by the SessionEnd write, as the desktop fields are.
- D2 — `asleep(role)` reports a CLI session whose recorded process is not running as `{ role, session, cli: true, worktree }`.
- D3 — `keel chat wake now <role>` runs `KEEL_CLAUDE` or `claude` with exactly `--bg --resume <session> "You have unread keel chat records; run keel context, then keel chat unread."` in the recorded worktree, and reports its output; for a running process it says so and runs nothing; for a role with no recorded CLI session it says so and exits 1.
- D4 — `keel tick` wakes each bound, unparked role that `asleep` reports CLI and that has an addressed unread record newer than the last one it woke the role for, recording that record id in `tick/state.json` under `woken.<role>`, so a role that does not read is not resumed again for the same record.
- D5 — A post, dm or todo that wakes a CLI-asleep role, and a patrol nudge escalation about one, say so and name `keel chat wake now <role>`; the desktop step stays for desktop sessions.
