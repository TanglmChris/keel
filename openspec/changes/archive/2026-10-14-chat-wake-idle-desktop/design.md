## Context

Issue #331; its own "Expected" names both shapes adopted here (print the wake step; tell the coordinator at once). Not chosen: Keel calling `send_message` itself (Keel launches nothing and has no host tool), and a new `authorize:` scope that would let the posting model send it unasked (a vocabulary change; left to the owner, see Follow-ups). #316 (parked roles nudged) is a separate change.

## Facts

- F1 — #320 comment 6171236953: a process-less desktop session saw no chat record for three minutes; `send_message` resumed it in 9 s.
- F2 — The desktop app sets `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and `CLAUDE_CODE_HOST_SESSION_ID=<id>` in the Claude process environment, which its hooks and Bash commands inherit (read 2026-10-14 in this session: `local_a4222dad-…`). `shift.js` already reads both (`desktopSession()`) and finds the session's Claude process by walking ancestors (`desktopProcess()`).
- F3 — Presence is written only by its own role's hooks and commands (`touchPresence`), and the SessionEnd hook marks it offline.
- F4 — `store.wakes(record, role)` is the one definition of whom a record wakes (mention, todo assignee, direct-group member).

## Decisions

- D1 — `touchPresence` records `desktop_session` and `desktop_pid` from the current environment when it is the desktop app, and clears both when it is not, so a role that moved to a terminal does not keep a stale id. The SessionEnd write keeps the previous values, since an ended session is exactly the one that needs waking.
- D2 — A role is asleep when its presence records a `desktop_session` and its `desktop_pid` is absent or not running. Presence lives in the repository's own `.git`, so the pid is checked on the machine that recorded it.
- D3 — After a post, dm, or todo, for each bound role the record wakes that is asleep, the output says the record alone wakes nothing (#331) and names: `get_session` on `<id>`; `unarchive_session` when it reports the session archived; then `send_message` to `<id>` asking it to run `keel chat unread`. Such a role is not also reported as `Queued … offline`. `--json` adds `asleep: [{role, session}]`.
- D4 — When `keel patrol --nudge` sends any nudge to an asleep role, it adds the risk `<role>'s desktop session <id> has no running process, so the nudge wakes nothing: get_session, unarchive_session if archived, then send_message to <id>`. It rides the nudge's own rate (unread at most once per two hours), so it repeats no faster than the nudge.
- D5 — The SessionStart hook moves the pid forward, so a woken session is no longer asleep.
