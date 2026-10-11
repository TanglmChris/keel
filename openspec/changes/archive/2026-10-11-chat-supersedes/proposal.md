## Why

Issue #252, part of #250 (rtl_ppa_prj, 2026-10-05): a changed division-of-work rule never reached the session it affected, and two sessions asked again a question already answered. Records already carry a system id and time and can reply, but a record cannot say it replaces an earlier one, and the unread list and the wake notice list the oldest first with stale records beside current ones.

## What Changes

- `keel chat post <group> <text> --supersedes <id>` posts a record that replaces an earlier record by the same author in the same group. The earlier record is kept.
- `keel chat <group>` shows a superseded record as superseded and names its successor. The successor names what it supersedes.
- A superseded record is no longer unread: `keel chat unread`, the wake notice, the waker, and every other reader of unread records skip it, so nobody acts on the old version.
- `keel chat unread` and the wake notice list newest first.
- The Slack copy of a superseded record is updated to say it was superseded and by which record.

## Capabilities

### Modified Capabilities
- `keel-cross-host-mailbox`: records can supersede earlier ones, and unread lists newest first.

## Impact

`src/core/chat/store.js`, `src/core/chat/view.js`, `src/core/chat/cli.js`, `src/core/chat/notice.js`, `src/core/chat/bridge.js`, `scripts/validate_plugin.py`, `README.md`, the published spec, and the changelog.
