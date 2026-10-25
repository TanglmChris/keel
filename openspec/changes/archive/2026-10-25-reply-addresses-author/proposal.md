## Why

Issue #468, approved by the owner on 2026-10-25. In kaiwu-ip on 2026-10-25 (Keel 5.201.0), `kaiwu-pm-iecc` asked `kaiwu-verify-iecc` to check and close two tickets. verify closed them at 20:26 and answered with `keel chat post iecc "…" --reply-to 20261025T122259189Z-kaiwu-pm-iecc-412472`, without writing `@kaiwu-pm-iecc`. The record carried `reply_to:` and no `mentions:`. PM's session was idle, so nothing woke it, and PM only learned of the answer when the owner asked. Another reply from verify the same evening did write `@kaiwu-pm-iecc`, and PM was woken at once. A reply is addressed to the record it answers, and the store did not treat it that way.

## What Changes

- **A reply mentions the author it answers.** When `keel chat post … --reply-to <id>` answers another role's record, and that role is a member of the group, the reply's `mentions` include that role, as if the text had written `@role`. So the notice, the hooks, `notice --check`, the waker, and acknowledgements all treat the reply as addressed to that role. A reply to one's own record adds nothing.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`

## Impact

The change touches `src/core/chat/store.js`, `scripts/validation/chat.py`, `scripts/validation/registry.py`, the published spec, and the changelog. The mention is written into the record, so an older Keel reading the store honors it as well.
