## Why

Issue #399: after 5.167.0 the owner still saw several `keel-maint` rows. Every shift session runs with Remote Control, and when the hand-over wakes the old session for its `/rename`, the bridge reconnects and writes the claude.ai title back over the rename (measured on the real old session and on a probe). The owner chose to name the new session for its start instead.

## What Changes

- The hand-over starts the new session as `<role> · <MM-DD HH:MM>`, its local start time, and records that name.
- The old session is stopped and no longer woken for a rename; the rename step, its waits and its "rename not shown" record go.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: the CLI hand-over names the new session for its start and does not rename the old one.

## Impact

`src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md` and its zh-CN twin, the published spec, the changelog.
