## Why

Issue #490, approved by the owner on 2026-10-27, who chose to judge by each session's record. In ChipSTRIDE three Claude Code sessions started in the main checkout, bound to `chipstride`, and two of them then entered their own worktrees and ran `keel chat role --set chipstride-be` and `--set chipstride-fe`. Their new bindings and session records were right, but `presence/chipstride.sessions.json` still listed all three, so `keel context` and every `keel chat post/unread/read` warned that three live sessions were bound to `chipstride`, when one was. A warning that is usually false trains everyone to ignore the one that is true.

## What Changes

- **The twin-session warning counts a session under a role only while that session's record does not name another role.** A session whose `sessions/<id>.json` names a different role — it moved with `keel chat role --set` — is not counted, so the warning no longer fires for it.
- A session whose record names the role, or that has no record, is counted as before, so two real sessions on one role are still reported.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`

## Impact

`src/core/chat/notice.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, the published spec, and the changelog.
