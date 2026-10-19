## Context

The CLI hand-over (#388) stops the old session, renames it by resuming it with `/rename`, stops it again, and starts a new session. #395 added a wait between the stop and the resume. Old sessions are kept and findable by the owner's decision of 2026-10-19; Keel also keeps a gzip copy of each transcript in its store (#343).

## Facts

- F1 — On a throwaway haiku background session (Claude Code 2.1.303, 2026-10-20), `claude stop` returned at 0.66 s, its row lost `status` at 0.83 s, and its pid (`claude bg-spare …`) exited at 2.68 s.
- F2 — Two probes that resumed for `/rename` once the row had no `status` still printed `already running in the background, so this started a copy as …` and left a running copy carrying the new name; one that resumed after the process had exited kept its id, and after `claude stop` still showed the new name (`~/.claude/jobs/<id>/state.json` `name` and the transcript's last `custom-title` both read it).
- F3 — In `claude agents --json --all`, a live row carries `status` and `pid`; a stopped one has neither. Every row carries `kind` (`background` for all 17 rows on 2026-10-20), `cwd`, `sessionId`, `startedAt`.
- F4 — `claude rm <id>` removes the row and leaves the session's transcript under `~/.claude/projects/…` (checked on four removed sessions, 2026-10-20). The host deletes transcripts after its cleanup period, which is what Keel's kept copy covers (#343).
- F5 — Owner, 2026-10-20: keep the most recent N old shifts per role, N in `keel/config.yaml`, default 3; and "即使不在 agent list 的 session，我也要能查完整内容".

## Decisions

- D1 — `retire()` takes the pid from the row it was handed (before the stop). After `claude stop` it waits until that process has exited, for at most `KEEL_SHIFT_STOP_WAIT_MS` (default 30 s); a row with no pid (already stopped) falls back to the listing showing no `status`. A process still running at the bound is not resumed; the rename is recorded as not shown and the hand-over goes on.
- D2 — `shift: keep_old_sessions: <n>` in `keel/config.yaml`, a whole number ≥ 0, default 3; any other value is ignored with a message and 3 applies. After a hand-over is delivered, the old sessions are the rows of `claude agents --json --all` with `kind: background`, no `status`, a `cwd` that is one of the role's bound worktrees, and a session other than the new one. Sorted newest `startedAt` first, the first n stay. Each other one is removed with `claude rm <id>` only when Keel's store holds a copy of its transcript, written now from the host file when missing; one whose transcript cannot be found or copied stays. The removed ids are recorded on the queue entry as `removed` and shown by `keel shift status`. Removal is the hand-over's step only: `keel tick` and `keel patrol` remove nothing on their own.
- D3 — `keel shift history <role> --show <id>` takes a session id or its 8-character prefix, matched against the transcript file names of the role's segments (recorded and found). It prints a header with the transcript and its time span, then every conversation record in file order: `[<timestamp>] <speaker>:` and the full text; a tool call prints as `[tool <name>] <its input as JSON>` and a tool result as `[result] <its text>`, each in full. It reads the host's file when it exists and Keel's kept copy otherwise. No match, or more than one, exits 1 naming the candidates.
