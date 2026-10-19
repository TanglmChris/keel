## Context

#388 lists what the owner saw on 2026-10-19. The tick's 300 s interval is host-scheduler cadence, right for the patrol and wrong for a hand-off the session has just asked for.

## Facts

- F1 — `claude agents --json --all` takes about 0.15 s. A live row carries `status` (`busy`/`idle`) and `state` (`working`/`done`/`idle`); an ended one has `state: stopped` or `done` and no `status`. A session blocked on `AskUserQuestion` reads `status` idle with `state` `working` (its job timeline's last state before `stopped from session`).
- F2 — `claude --bg --resume <full id> "/rename X"` with no other flag keeps the session id and `claude agents` shows `X` within 4 s; `claude stop` afterwards keeps it. `claude -p --resume … "/rename X"` renames only the transcript, not the listing. Passing any flag with `--resume` makes a copy. Measured 2026-10-19, Claude Code 2.1.303.
- F3 — A Bash tool's environment carries the session's `CLAUDE*` variables, among them `CLAUDE_CODE_SESSION_ID`, `CLAUDE_PID`, `CLAUDE_JOB_DIR` and a messaging token. A process started from it passes them on.

## Decisions

- D1 — `ready --wake` on the CLI spawns `keel shift handover-wait --role <role> --repo <worktree>`, detached, with cwd `/` and an environment without `CLAUDE*` variables (F3), so the claude it starts is not mistaken for a child of the old session. It runs the hand-over every `KEEL_SHIFT_HANDOVER_POLL_MS` (default 3000) until the entry is no longer pending or `KEEL_SHIFT_HANDOVER_TIMEOUT_MS` (default two hours) passes.
- D2 — A hand-over holds `queue/<role>.lock`, created exclusively; a lock younger than two minutes makes the other runner skip the entry, an older one is replaced. The entry stays `pending` until `delivered` or `failed`.
- D3 — The old session is finished when it is gone from `claude agents --all`, or its `status` is not `busy` and its `state` is absent, `done`, `idle` or `stopped`. Anything else waits.
- D4 — Retire: stop the old session, resume it with `/rename` (F2), poll `claude agents --all` once a second for up to 30 s until its name is the new one, stop it again; only then start the new session, so a resumed old session's hooks cannot overlap the new one's. The name is `<role> · shifted <YYYY-MM-DD HH:MM>`. A rename that does not show is recorded in the entry (`rename`) and reported by `keel shift status`; the hand-over goes on.
- D5 — `keel shift status` says a pending hand-off has no waiter or tick to carry it out only when it can tell: it cannot, so it does not. What it does say is the age of a pending one, so the 15-minute patrol risk keeps its meaning.
