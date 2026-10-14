## Context

Issue #324 comments 6164793777 and 6165454422; `~/Library/Logs/Claude/main*.log`. Not chosen: keeping the step and documenting the wait (it keeps a person in the loop for nothing the clear needs); reporting upstream only (the step can go now; the description's claim is worth reporting separately).

## Facts

- F1 — Every `set_remote_control(…, false)` from 2026-10-06 to 2026-10-14 logs `Emitted tool permission request … set_remote_control`, and `Disabling remote control` follows only when it resolves (`once` clicked in the app, or `aborted` when answered elsewhere). `true` calls log no request. The allow rule is present throughout.
- F2 — 2026-10-14 17:14:28: `Clearing session local_61cdaac8…` with Remote Control on (enabled 17:11:24) and no viewer; accepted, no permission request.
- F3 — 17:34:57 `Reconnecting Remote Control for local_61cdaac8… after /clear` → enabled under a new address.
- F4 — 17:35:37: second clear with the owner viewing on the phone; accepted on the desktop, the phone kept the old conversation.
- F5 — Whether a session cleared and then started by a partner's `send_message` (not typed into) also reconnects is not measured; sessions that came back with Remote Control off on 2026-10-13 had it turned off before their clear.

## Decisions

- D1 — The desktop hint has three steps: create the one-shot wake task (prompt unchanged from 5.133.0); rename; clear. It says to rename and clear right after creating the task, because a task that fires before the clear gets it refused. It no longer names `set_remote_control("self", false)`.
- D2 — The general clear hint drops "A session serving Remote Control cannot be cleared"; the desktop hint says Remote Control stays on across the clear and the app reconnects it under a new address, so a remote viewer opens the new one (#324).
- D3 — `resume` on the desktop app says to check Remote Control with `get_session` and turn it back on with `set_remote_control("self", true)` only if it is off (F5), and to rename the session back.
- D4 — `self-shift` covers the three steps; the hint says "these three steps".
