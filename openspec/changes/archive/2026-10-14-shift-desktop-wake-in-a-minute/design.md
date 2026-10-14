## Context

Owner, 2026-10-14: "我需要在1分钟内完成换班"; "mac休眠通过快速换班解，我们不考虑长间隔". Not chosen: a `fireAt` some seconds out (the minute tick still adds 0–60 s, and a fire before the clear refuses the clear); a partner that polls `get_session` (each poll is a model turn, and no field is known to flip exactly at the clear).

## Facts

- F1 — `main.log`: every `[CCDScheduledTasks] Spawning new session` from 2026-10-13 to 2026-10-14 lands at :16–:23 past a minute, one-shot tasks included (fireAt 10:06:44Z → spawned 18:07:23 local).
- F2 — `run_scheduled_task` starts a run "right now, the same as Run now", returning the new run's session id; it is refused only for a disabled, deleted, or busy task. An ad-hoc task (neither `cronExpression` nor `fireAt`) is never dispatched by the schedule.
- F3 — The session's tools run under a Claude CLI process that is an ancestor of the Bash shell (`ps`: zsh 36953 → `…/claude-code/2.1.295/…/claude` 98855 → Claude.app helper). That process started at 18:07:52, the second the woken session was cold-started; the `clear_session` description and F4 say the clear stops the session.
- F4 — 18:01:09 `Stopping session …` / `Clearing session …` / `query iterator completed`, then 18:07:52 `sendMessage on uninitialized session; cold-starting via startSession`.
- F5 — `clear_session("self")` happens when the turn ends and the session is idle, and is dropped if a message is already waiting; so any send must follow the clear.
- F6 — 18:07:23 run spawn → 18:07:52 send → 18:08:00 first assistant turn: about 29 s of run, including an unarchive, and 8 s of cold start.

## Decisions

- D1 — `ready` on the desktop app walks its ancestors to the nearest process whose command's basename is `claude` and records `Desktop process: <pid>.` in the note; `KEEL_SHIFT_DESKTOP_PID` overrides it, for tests. When none is found the recipe says so and that the new session must be typed into.
- D2 — `keel shift await-clear --pid <pid> [--timeout-ms n]` checks the process every 250 ms; exits 0 with `cleared` once it is gone, 1 with `not cleared` after the limit (default 120 000 ms).
- D3 — The recipe: (1) create, or update when it exists, the ad-hoc task `keel-shift-wake-<role>` with no `fireAt` or `cronExpression` and `notifyOnCompletion: false`, whose prompt runs `keel shift await-clear --pid <pid>` with Bash first; on exit 1 it sends nothing, calls `PushNotification`, and starts its reply with `WAKE FAILED`; on exit 0 it does the 5.135.0 wake (get_session → unarchive if archived → send_message → delivery check); (2) `run_scheduled_task` on it at once; (3) rename; (4) clear. It says the run waits for the clear itself, so starting it first is safe, and that the shift takes well under a minute.
- D4 — The overdue default in `keel shift status` becomes 3 minutes.
- D5 — `self-shift` covers the four steps; the unattended line adds `mcp__scheduled-tasks__run_scheduled_task`.
- D6 — The one-minute claim is measured on a real self-shift with this branch's Keel before the change closes; the woken session records the log times on #326.
