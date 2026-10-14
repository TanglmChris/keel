## Context

Issues #324, #326; the 2026-10-14 18:00 run in `~/Library/Logs/Claude/main.log`. Not chosen: a Keel-side watchdog process that re-sends (Keel schedules nothing beyond the one waiter, and on the desktop app only a host prompt starts the session); keep-awake from the outgoing session (`request_keep_awake` ends when the session is stopped, which the clear does).

## Facts

- F1 — 18:01:09 clear; 18:02:35 `AutoArchiveEngine` archived the session; 18:07:23 the wake task's run started; 18:07:38 `Unarchived session`; 18:07:52 `sendMessage on uninitialized session … cold-starting`, `Reconnecting Remote Control … after /clear`; no `Emitted tool permission request` for either session from 18:00 to 18:08.
- F2 — The host's `send_message` result names the delivery: `delivered` (the target's turn started on it), `queued` (it runs after the target's current work), or an error saying why it was not delivered.
- F3 — `list_task_runs` reports a run's status and a one-line summary, which is the run's own text.
- F4 — `request_keep_awake` holds only until its session is stopped or archived; the clear stops the outgoing session.

## Decisions

- D1 — The wake prompt treats `delivered` or `queued` as a delivered wake. Any other result, after the archived retry, is a failed wake: the task calls `PushNotification` with the session id and the result, and starts its reply with `WAKE FAILED`, so the run summary carries it (F2, F3).
- D2 — `keel shift status` reads `Desktop session:` from a waiting note; past the overdue time (15 minutes after the note was written; `KEEL_SHIFT_WAKE_OVERDUE_MS` overrides it for tests) the row says the desktop wake is overdue and names the session id, `list_task_runs`, and `send_message`. It covers the wake that never ran, which D1 cannot see.
- D3 — Repeating the end-to-end run with a long gap and the app in the background is measurement, not code; #326 owns it.
