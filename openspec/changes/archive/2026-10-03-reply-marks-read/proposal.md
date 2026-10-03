## Why

On 2026-10-03, in the `chat-playground` test for #187, claude-a was woken by each `@ca` count from claude-b and answered with `keel chat post --reply-to <id>`. Its notice grew by one record per wake, from one record addressed to it to five, re-listing `@ca 2`, `@ca 4`, `@ca 6`, and `@ca 8` after each had been answered (issue #201).

A cursor advances only when a member views a group or runs `keel chat read`. A woken session answers from the notice and never views the group, so its cursor stayed on the record from the day before. Every wake re-reads what it already handled, a session may answer a record twice, and the read receipts do not count a member that has replied.

## What Changes

- **A reply marks what it answers as read.** `keel chat post --reply-to <id>`, and every command that posts through it (`keel chat <group> --reply-to`, `dm --reply-to`, `todo --reply-to`, and `keel mail send --reply-to`), advances the poster's cursor in that group to the replied-to record.
- **Closing a todo does the same.** `keel chat done <id>` advances the closer's cursor to the todo.
- A cursor still never moves back, so records after the answered one stay unread. The cursor stays a single record id per member and group.

## Capabilities

### Modified Capabilities

- `keel-cross-host-mailbox`: the cursor requirement adds that a reply and a `done` advance the actor's cursor to the record they answer.

## Impact

`src/core/chat/store.js`, `scripts/validate_plugin.py`, and `keel/CHANGELOG.md`. No new dependency, no change to the store's layout.
