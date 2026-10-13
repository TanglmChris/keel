## Why

Issue #319, end-to-end test of 5.127.0 on 2026-10-13 (comment 6138487679). The printed desktop recipe was followed twice, and both times `clear_session("self")` waited for the owner's approval: once for 13 minutes, once for 1 h 40 min. Remote Control was already off, so the owner could not approve it away from the desk. The partner's scheduled wake fired meanwhile, and the app queued its `send_message` as a user message. When the clear was finally decided, the app refused it to protect that message. The owner then added `mcp__ccd_session_mgmt__clear_session` to `permissions.allow`. Owner decision, 2026-10-13: allow the clear and name it in the recipe.

## What Changes

- On the desktop app, the `ready --wake` partner step also names `mcp__ccd_session_mgmt__clear_session` as a `permissions.allow` entry, and says why: a clear left waiting for approval lets the wake arrive first, and the app then refuses the clear.
- `docs/shift-change.md` and its Chinese translation say the same.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the desktop recipe names both allow entries it depends on.

## Impact

`src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
