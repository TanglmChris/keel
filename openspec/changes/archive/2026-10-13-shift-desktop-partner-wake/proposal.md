## Why

Issue #319 (2026-10-13): on the Claude desktop app, `keel shift ready --wake` never brings the next shift up. `clear_session` ends the Claude Code session, and the app starts the next one only when a prompt arrives; the waiter waits for a session start that only a prompt produces, so it waits forever. The `ready` output still says "The wake is armed". A live test the same day showed the gap closes from outside: a one-shot desktop scheduled task whose prompt calls `send_message` to the cleared session's id started it 7.5 s after the task fired. The same test showed that Remote Control does not come back after the clear, and the woken session can turn it on only when `mcp__ccd_session_mgmt__set_remote_control` is in `permissions.allow`. Owner decision, 2026-10-13: fix it with that partner wake. Keel prints the recipe and launches nothing.

## What Changes

- `keel shift ready`, run in the Claude desktop app (`CLAUDE_CODE_ENTRYPOINT=claude-desktop` with `CLAUDE_CODE_HOST_SESSION_ID` set), records the desktop session id in the note.
- With `--wake` there, the clear hint stops promising that the waiter wakes the new session. It prints the partner recipe instead: a one-shot scheduled task, created before the clear, whose prompt calls `send_message` to that session id with the resume instruction and asks the woken session to turn Remote Control back on first. It also names the allow rule that last step needs.
- `keel shift resume`, run in the desktop app, reminds the new shift to turn Remote Control back on.
- `docs/shift-change.md` and its Chinese translation describe the desktop recipe.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: a self-shift on the desktop app is told how its next session gets started, and the resumed shift is told to restore Remote Control.

## Impact

`src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
