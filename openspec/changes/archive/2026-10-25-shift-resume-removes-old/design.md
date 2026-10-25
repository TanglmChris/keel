## Facts

- F1 — `removeOldSessions` (`src/core/shift.js`) runs only from `deliver()`, the end of a Keel-run hand-over. `resume` never calls it (origin/main `f5dc6b3f`, 5.198.0).
- F2 — It picks rows by `bound.has(realpath(row.cwd))`, where `bound` holds the role's worktrees from `roles.json`. On 2026-10-25, after the rename, `roles.json` names `/Users/my_home_mac/my-github/...`. The listed rows (Claude Code 2.1.307) still carry `cwd: /Users/my_home_mac/my_github/...`, a directory that no longer exists, and `realpath` of a missing path returns it unchanged.
- F3 — Keel keeps each role's ended transcripts at `keel-chat/shift/transcripts/<role>/<session id>.jsonl.gz` (`keptFile`, #343). On 2026-10-25 that directory held `6fffda34-….jsonl.gz` for `keel-maint`, the session left listed.
- F4 — `hostTranscript` maps both `_` and `-` in a path to `-`, so the host's transcript of a pre-rename session is still found under the renamed project directory.
- F5 — The note records `CLI session: <id>.` and `CLI process: <pid>.` when a CLI session wrote it (`ready`). The new session's process carries `CLAUDE_CODE_ENTRYPOINT` and `CLAUDE_CODE_SESSION_ID`. The validation scenarios remove both from the environment (`chat_environment`).
- F6 — In a Keel-run hand-over, `deliver()` has already removed old sessions and recorded `new_session` (the job id) on the role's queue entry before the new session runs `resume`.

## Decisions

- D1 — `resume` removes old sessions when four things hold: the worktree has a role, the printed note names a `CLI session`, the process runs under a Claude Code host (`CLAUDE_CODE_ENTRYPOINT` is set), and the role's queue entry is not a `delivered` hand-over whose `new_session` begins the current session id. The last one is F6: that hand-over already removed them. It calls `removeOldSessions` with the note's session as the one handed over, the note's process for the bounded exit wait, and the current session's job id as the new one, under the declared `keep_old_sessions`. With no host answer, nothing is removed and `resume` still succeeds.
- D2 — A stopped background row is the role's when its `cwd` is a bound worktree, or when `keptFile(where, role, <sessionId>.jsonl)` exists. This holds for both callers. Every other guard stays: a transcript somewhere, Keel's copy before `rm`, no running process, not the new session.
- D3 — `resume` prints `Removed old sessions from claude agents: <ids>; keel shift history <role> --show <id> prints each.` when it removed any, and returns them as `removed` in `--json`. It prints nothing otherwise.
- D4 — Rejected: a cleanup that sweeps every role, or a new command. The freeze rules out a new command. A sweep would remove another role's sessions on a guess, while each role's own `resume` already covers its leftovers.
