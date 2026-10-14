## Why

Issue #324. The desktop self-shift recipe turns Remote Control off before the clear, because the `clear_session` description says a session serving a Remote Control client cannot be cleared. That step is the one an unattended shift cannot pass: every `set_remote_control(…, false)` since 2026-10-06 (16 calls) raised an app permission request that `permissions.allow` does not skip, and returned only when someone answered it — after 13 min, 1 h 40 min, 3 h 36 min (#324 comment 6164793777). On 2026-10-14 the owner measured the premise in a fresh desktop session and it did not hold: with Remote Control on, `clear_session("self")` was accepted twice, once with nobody viewing and once with the owner viewing on the phone, and the app reconnected Remote Control by itself after the clear, under a new remote address (#324 comment 6165454422). Owner decision, 2026-10-14: if the clear is accepted either way, drop the step.

## What Changes

- The desktop `ready --wake` recipe drops the Remote Control step: create the wake task, rename, clear — three steps, the last two right after the task.
- The general clear hint no longer says a session serving Remote Control cannot be cleared; on the desktop app it says the app reconnects Remote Control after a clear, under a new address a remote viewer has to open.
- `resume` on the desktop app says to turn Remote Control back on only if it is off, and still to rename the session back.
- `self-shift` covers the three steps.
- The unattended line keeps `set_remote_control` (the woken session may still need it), `get_session` and `unarchive_session`.
- The docs, the README vocabulary, and the `keel/config.yaml` comments follow.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the desktop recipe and the resume restore.
- `keel-standing-authorization`: `self-shift` covers three steps.

## Impact

`src/core/shift.js`, `keel/config.yaml`, `README.md`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, both published specs, and the changelog.
