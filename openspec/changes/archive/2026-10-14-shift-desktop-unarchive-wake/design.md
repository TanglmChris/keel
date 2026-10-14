## Context

Issue #326 comments 6163643615, 6163697376 and 6163730805, and the long-gap test of 2026-10-14 (desktop session `local_a4222dad-…`, wake task `keel-maint-self-shift-long-gap`), read from `~/Library/Logs/Claude/main.log` and the outgoing shift's transcript. Not chosen: asking the owner to turn off auto-archive (it is the owner's setting and serves other sessions); turning the per-PR `auto_archive_on_close` switch off (it needs a bound open PR, and the engine archived with nothing bound); keeping the dismiss step as "best effort" (a step whose success signal is false trains the reader to trust it).

## Facts

- F1 — 2026-10-14 15:39:14: `[AutoArchiveEngine] Holding local_a4222dad-… (PRs #282,…,#315,#330 …)` — 20 PRs, although all 20 were dismissed on 2026-10-13 (F3 of the archived `shift-desktop-unbind-merged-prs`). The dismissals had not persisted into the engine's set.
- F2 — 15:43:13 `unbind_pr` #330 → "Dismissed … from this session's PR bar"; `get_status` then read `bound: false`.
- F3 — 15:44:26 clear. 15:46:33 the session was focused; 15:46:34 `getPrChecks … prNumber=330`; 15:47:02 `[AutoArchiveEngine] Archiving local_a4222dad-… (PRs #282,…,#330 …) (PR merged)`, worktree released to the pool ("verified clean").
- F4 — 15:51:40 the wake task ran; 15:52:05 `Unarchived session`; 15:52:10 `[rebindWorktree] Rebound … on branch claude/keel-optimization-maintenance-0cb8d4` ("untouched since parked"); the send was delivered and the woken session restored Remote Control (15:52:38) and its title (15:52:54).
- F5 — `get_session` returns the session's metadata; `unarchive_session` "restores an archived CCD session …; a worktree removed at archive is … re-acquired on its next turn (local)".

## Decisions

- D1 — The desktop hint drops the dismiss step. It has four steps: Remote Control off and wait; create the task; rename; clear.
- D2 — The task's prompt first calls `get_session` on the session id, and when it reports the session archived, calls `unarchive_session` on it; then `send_message`; if that send is still refused because the session is archived, it unarchives and sends once more. It says which path it took. The hint gives the reason: the app's auto-archive can archive the cleared, idle session before the wake (#326), and unarchiving brings back the same worktree.
- D3 — The unattended line names `mcp__ccd_session_mgmt__set_remote_control`, `mcp__ccd_session_mgmt__get_session` and `mcp__ccd_session_mgmt__unarchive_session` under `permissions.allow`, and `shift-restore` under `authorize:`. It no longer names `mcp__ccd_pr__unbind_pr`.
- D4 — `self-shift` covers the four steps; the hint says "these four steps".
