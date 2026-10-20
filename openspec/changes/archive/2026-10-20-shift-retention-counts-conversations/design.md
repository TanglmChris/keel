## Context

5.167.0 (#397) keeps the newest `shift: keep_old_sessions:` stopped background sessions in a role's bound worktrees. It removes each older one with `claude rm` once Keel's store holds a copy of its transcript, and leaves a session whose transcript cannot be copied.

## Facts

- F1 — d6bedfc8, in keel-maint's worktree: `~/.claude/jobs/d6bedfc8/state.json` reads `"detail": "(idle — send a prompt to start)"` and was created at `2026-10-19T23:44:40.797Z`, 0.7 s after the old shift ran `claude --bg --help`. No transcript for it exists under `~/.claude/projects/`. `claude agents --json --all` listed it as a background row with no `status`.
- F2 — The 08:08 hand-over's queue entry reads `removed: ["2b7acbb6"]`. The kept rows were 61d93a31, d6bedfc8 and b4d145a2 (newest `startedAt` first), so with d6bedfc8 not counted, 2b7acbb6 would have been the third.
- F3 — Keel's copy of a transcript is `shift/transcripts/<role>/<session id>.jsonl.gz` in the chat store (`keptFile`), so it can be found from the session id alone.

## Decisions

- D1 — The old sessions counted toward `keep_old_sessions` are the rows chosen as before that also have a conversation: a host transcript, or Keel's copy at `shift/transcripts/<role>/<session id>.jsonl.gz`. A row with neither is not counted and not removed.
- D2 — A counted row beyond the kept ones is removed when Keel's store holds its copy: one is written from the host transcript when that exists, and when it does not, the copy already there is enough. A row whose copy cannot be written stays, as before.
