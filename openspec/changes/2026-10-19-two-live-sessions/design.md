## Context

#369 suggested warning on `keel context`, `keel chat post` and `keel chat read`, or keying presence and cursors by session. Keying the cursor by session would change who has read what for every existing store; a warning is the part that would have stopped the incident.

## Facts

- F1 — `touchPresence` (`src/core/chat/notice.js`) rewrites `presence/<role>.json` on every hook event and chat command; it keeps one record per role.
- F2 — A CLI session's environment carries `CLAUDE_CODE_SESSION_ID` and `CLAUDE_PID`; a desktop one `CLAUDE_CODE_HOST_SESSION_ID`, its process found by `desktopProcess()`.

## Decisions

- D1 — `presence/<role>.sessions.json` maps session id to `{ pid, worktree, host, last_active }`. `touchPresence` updates the writer's entry when a session id is known, removes it on the SessionEnd write, and prunes entries whose recorded pid is not running or whose last activity is over 24 hours old.
- D2 — A session is live when its pid is running, or, with no pid, when it was active in the last 30 minutes.
- D3 — With two or more live sessions, the warning reads `<n> live sessions are bound to role <role>: <id> (pid <p>, <worktree>), …. They post under one name and share one read cursor, so one can hide unread records from the other; stop one, or bind it to another role with keel chat role --set.` `keel context` adds it to `warnings`; `post`, `dm`, `todo`, `unread` and `read` write it to stderr, so JSON on stdout stays intact.
