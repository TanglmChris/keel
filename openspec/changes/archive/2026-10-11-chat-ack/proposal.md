## Why

Issue #253, part of #250 (rtl_ppa_prj, 2026-10-05), absorbing #247: about 20 messages in one day, with several resends because silence looked like work in progress. Keel keeps per-role read cursors (`keel chat show` lists who has read a record), but a sender cannot ask for an acknowledgement or tell "read and agreed" from "read" or "not read".

## What Changes

- `keel chat post … --ack` (and `todo … --ack`) asks the roles a record addresses to acknowledge it: those it mentions, the members of `@all`, a todo's assignee, and the other member of a direct group.
- A recipient acknowledges with `keel chat ack <id>`, or by replying to the record. An acknowledgement marks the record read for that role, is a record of its own, and wakes nobody.
- `keel chat show <id>` lists, for a record that asks, who acknowledged, who read without acknowledging, and who has not read. `keel chat acks [--mine]` lists records still waiting on someone, with the same three lists; `--mine` keeps those the caller posted.
- The wake notice and group views mark a record that asks for an acknowledgement.

## Capabilities

### Modified Capabilities
- `keel-cross-host-mailbox`: records can ask for an acknowledgement, and who has given it is listed.

## Impact

`src/core/chat/store.js`, `src/core/chat/cli.js`, `src/core/chat/view.js`, `src/core/chat/notice.js`, `src/core/chat/bridge.js`, `scripts/validate_plugin.py`, `README.md`, the published spec, and the changelog.
