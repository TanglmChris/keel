## Why

Issue #320, measured 2026-10-14: on the Claude desktop app a session with no running process (cleared, or paused on idle) never sees a chat record. `keel shift start start-probe` printed `Woke start-probe …` at 22:50:13 and the target showed no log line for three minutes; a `send_message` to its session id resumed it in 9 s. So on the desktop app `keel shift start` wakes nobody and says it did. The shift feature is frozen (owner, 2026-10-14) — this is a bug fix that reuses the partner step the self-shift wake already uses, with no new mechanism.

## What Changes

- When the waiting note records `Desktop session: <id>`, `keel shift start` still posts the start record, but its output no longer says it woke the role. It says a desktop session with no running process sees no chat record (#320) and prints the step to wake it: `get_session` on `<id>`, `unarchive_session` when archived, then `send_message` to `<id>` with the start text.
- Notes without a desktop session print as before.
- Both shift-change docs follow.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the coordinator's start on the desktop app.

## Impact

`src/core/shift.js`, `scripts/validate_plugin.py`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, the published spec, the changelog.
