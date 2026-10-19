## Why

A dry run of 5.159.0's `keel chat role --rename iecc-pm kaiwu-pm-iecc` on a copy of kaiwu-ip's chat store (2026-10-19) dropped `kaiwu-pm-iecc` from group `iecc`, and with it the one record it had unread. kaiwu-ip had added the new name to `iecc` and then removed the old one (#376's workaround). The log is read through the rename, so `leave iecc-pm`, written after `join kaiwu-pm-iecc`, read as the new role leaving. Every team that migrated by hand before the rename existed has that order.

## What Changes

- Group membership is computed under the names the `join` and `leave` records were written for, and then read through the renames. So a leave of the old name removes only the old name's membership.
- A role merged from several names is listen-only in a group only when every one of those names was.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`: a rename keeps a membership the new name already had.

## Impact

`src/core/chat/store.js`, `scripts/validate_plugin.py`, one published spec, the changelog.
