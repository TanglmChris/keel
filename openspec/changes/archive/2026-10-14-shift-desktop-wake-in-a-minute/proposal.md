## Why

Owner requirement, 2026-10-14: a desktop self-shift completes within one minute, and fast shifting is also the answer to the Mac idle-sleeping in the gap; long gaps are out of scope. The 5.135.0 recipe cannot meet it: its wake is a one-shot scheduled task with `fireAt` a few minutes out, and the app dispatches due tasks once a minute (`[CCDScheduledTasks] Spawning …` at about :17–:23 past every minute, `main.log`), so the wake lands 0–60 s after its time and the run then needs about 37 s (18:07:23 spawn → 18:08:00 first turn of the woken session on 2026-10-14). The fire time itself has to be minutes out only because a wake that arrives before the clear gets the clear refused.

## What Changes

- `keel shift ready` on the desktop app records the session's Claude process id in the note.
- New `keel shift await-clear --pid <pid>`: blocks until that process has exited, which is what the app's clear does to it, and exits 0; exits 1 after a time limit (120 s).
- The desktop recipe becomes four steps: create (or update) an ad-hoc wake task, with no schedule, whose prompt runs `keel shift await-clear` before anything else and only then unarchives if needed and sends; start it at once with `run_scheduled_task`; rename; clear. The wake waits for the clear itself, so it can start before it, and nothing waits for the minute tick.
- A wake whose `await-clear` times out sends nothing, calls `PushNotification` and starts its reply with `WAKE FAILED`.
- The overdue time in `keel shift status` drops from 15 to 3 minutes.
- `self-shift` covers the four steps; docs, README, and config comments follow.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: desktop recipe, `await-clear`, overdue time.
- `keel-standing-authorization`: `self-shift` covers four steps.

## Impact

`src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `README.md`, `keel/config.yaml`, `scripts/validate_plugin.py`, both published specs, the changelog.
