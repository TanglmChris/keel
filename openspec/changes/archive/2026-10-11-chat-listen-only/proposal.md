## Why

Issue #248 (rtl_ppa_prj review session, 2026-10-05): a review session needing the user's decision had to go through the PM — question to PM, PM asks in Slack, the user answers, PM relays back — and saw only the PM's paraphrase; the project traced three measurement misreports to paraphrasing. The owner decided on 2026-10-11: a listen-only membership flag per group, so the session receives the user's own wording while asking stays with the coordinator.

## What Changes

- `keel chat group add <group> <role> --listen` adds a listen-only member.
- A listen-only member receives the group's records, including Slack-imported ones, and is woken when addressed, like any member. It may acknowledge records and close todos assigned to it.
- It may not post or open a todo in that group, change its membership, or archive it; each is refused naming the flag. `keel chat group list` marks it.

## Capabilities

### Modified Capabilities
- `keel-cross-host-mailbox`: a group member can be listen-only.

## Impact

`src/core/chat/store.js`, `src/core/chat/cli.js`, `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
