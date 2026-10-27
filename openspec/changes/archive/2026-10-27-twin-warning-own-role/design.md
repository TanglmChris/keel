## Facts

- F1 — `touchSession` (`src/core/chat/notice.js`) lists each session that writes a role's presence in `presence/<role>.sessions.json`, with pid, worktree and last activity, and drops an entry only once its process has ended or it is a day stale.
- F2 — A session's record `sessions/<id>.json` is written at SessionStart with the role of the worktree it started in (`rememberSession`), and rewritten with the new role by `keel chat role --set` in a worktree whose host project holds the session's transcript (`recordBinding`, #415 D3).
- F3 — `twinWarning` counts every live entry of the role's list. A session that started under X and then bound Y stays in X's list until it ends, so X warns of it (#490).
- F4 — Commands already treat the record as the authority on whose a session is: `commandPresence` records a session under a role only when its record names that role (#415 D2).

## Decisions

- D1 — `twinWarning` counts a live entry only when the session's record names this role or no record exists. An entry whose record names another role is the session's past, not a twin.
- D2 — A missing record keeps the entry counted. This is narrower than counting only sessions whose record names the role: a session listed with no record cannot be told apart from a real twin, and the warning exists to catch that.
- D3 — The list itself is left as it is: the stale entry ages out when its process ends (F1), and `keel chat role --set` is not changed to edit another role's list.
