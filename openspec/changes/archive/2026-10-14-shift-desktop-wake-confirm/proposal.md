## Why

Issues #324 and #326. On 2026-10-14 the 5.134.0 desktop self-shift ran end to end with no person (18:01:09 clear, 18:02:35 auto-archived, 18:07:38 the wake unarchived it, 18:07:52 delivered, Remote Control reconnected by itself). One run is one sample, and every link of it rests on desktop-app behavior Keel does not control. Two failure shapes stay silent today: the wake task runs but its `send_message` does not deliver, and the wake task never runs at all. In both, the role sits cleared with its note waiting and nobody is told. Owner decision, 2026-10-14: close the Claude-side gaps in this change; Codex is parked.

## What Changes

- The desktop wake prompt confirms delivery: `send_message` reporting `delivered` or `queued` is a delivered wake; any other result after the archived retry is a failed wake, and the task calls `PushNotification` naming the session and the result and starts its reply with `WAKE FAILED`, so the run's summary shows it.
- `keel shift status` lists a note that records a desktop session and has waited past an overdue time (15 minutes) as an overdue desktop wake, naming the session, `list_task_runs` and `send_message`.
- The docs follow.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the desktop wake prompt and shift status.

## Impact

`src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
