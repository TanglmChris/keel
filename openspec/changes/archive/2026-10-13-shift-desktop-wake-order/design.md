## Context

Issue #319, its comments 6143435530 (timings in the maintenance session) and 6144856601 (probe session), and the owner's decisions of 2026-10-13. Not chosen: leaving the woken session to ask the owner; not restoring Remote Control at all. The first keeps the owner's phone view dark until they answer, and the second drops it entirely. Still open: why turning Remote Control off blocks in a session the owner follows remotely. The fix only makes the order robust to it.

## Facts

- F1 — `set_remote_control(false)` in the maintenance session returned after 13 min, 1 h 40 min and 3 h 36 min. Each `clear_session` returned within a second, and was refused because the earlier-created wake was queued.
- F2 — In the probe, `set_remote_control(false)` returned in 5 s, the task was created after it, and `clear_session` was accepted. The wake at about 19:35 started a new transcript at 19:36:29.
- F3 — The woken probe ran `keel context` and `keel shift resume`. It then asked the owner (`AskUserQuestion`, 19:36:53 → 19:47:49) before `set_remote_control(true)`, because the instruction came from a session message and a note.
- F4 — Owner, 2026-10-13: after several self-shifts the session list showed same-titled sessions, some archived. Rename the outgoing session before the clear.

## Decisions

- D1 — The desktop `--wake` hint replaces its partner sentence with four ordered steps:
  1. `set_remote_control("self", false)`, and wait for it to return.
  2. Only then `create_scheduled_task`, firing about three minutes later, with the `send_message` prompt. The step says why: a task created earlier can fire first, and the app then refuses the clear to keep that message.
  3. `set_session_title` on this session, e.g. `<role> · shifted <time>`.
  4. `clear_session("self")`.

  It then names `mcp__ccd_session_mgmt__set_remote_control` under `permissions.allow` and `shift-restore` under `authorize:`. It no longer names `mcp__ccd_session_mgmt__clear_session`.
- D2 — The wake message asks the woken session to run `keel context` and `keel shift resume`, then restore Remote Control and its title as `resume` says. The restore follows `resume` because `resume` is where the repository's authorization is read (F3).
- D3 — `shift-restore` joins `STANDING_AUTHORIZATION_ACTIONS` with no scope. A scoped form is refused as `unexpected-scope`, like the other unscoped names.
- D4 — `resume` on the desktop app appends one of two lines. With `shift-restore` declared: `Standing-authorized by \`shift-restore\` in keel/config.yaml: turn Remote Control back on with set_remote_control("self", true) and rename this session back to its working title with set_session_title, now, without asking.` Without it: `On the Claude desktop app a clear keeps neither Remote Control nor this session's title: turn Remote Control back on with set_remote_control("self", true) and rename the session back with set_session_title. Declaring \`shift-restore\` under authorize: in keel/config.yaml lets a woken session do this without asking.`
- D5 — This repository declares `shift-restore` in `keel/config.yaml`, by the owner's decision of 2026-10-13.
