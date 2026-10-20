## Context

#388 renamed the retired session `<role> · shifted <time>` by resuming it with `/rename`; #395 and #397 made that resume wait for the stop and then for the process. All shift sessions on this machine run with Remote Control (`remoteControlAtStartup: true` in the owner's settings).

## Facts

- F1 — b4d145a2, resumed with `/rename` after its process had exited, showed the new name for under 8 s and then `keel-maint` again while still running; its transcript reads `custom-title` (new), `custom-title` (`keel-maint`), `bridge-session` (Claude Code 2.1.303, 2026-10-20).
- F2 — A haiku probe started as a hand-over starts a session had a `bridgeSessionId`; the same rename flow wrote the new title and then the old one, and the listing never showed the new name.
- F3 — The name a session is started with (`-n`) is the one that reaches claude.ai: b4d145a2's server title is its `-n keel-maint`.
- F4 — Nothing in Keel reads a session's name; a role is bound to a worktree (`roles.json`).

## Decisions

- D1 — The hand-over starts the new session with `-n "<role> · <MM-DD HH:MM>"`, the local time at start, and records it as `new_name` on the queue entry; `keel shift status` shows it beside the new session id.
- D2 — Retiring the old session is `claude stop` alone. It is not resumed, so neither a rename nor its waits remain, and entries no longer carry `renamed`; an entry written before this change still shows what it recorded.
