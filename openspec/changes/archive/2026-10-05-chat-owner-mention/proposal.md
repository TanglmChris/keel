## Why

On 2026-10-05 the owner asked how Slack notifies them. With Slack's default notification setting, a channel message notifies them only when it mentions them, and the bridge turns a record's `@owner` into a real mention. Nothing tells a session this, so whether a message the owner must see reaches their phone depends on whether that session happened to write `@owner`. The owner asked for it to become the rule: a Slack message the owner needs to know about mentions them.

## What Changes

- For a Slack-enabled project whose `keel/chat.json` names an owner, the session-start notice carries one line saying that Slack notifies the owner only for messages that write `@owner`, so a message the owner needs to see or decide on writes it and routine discussion does not.
- Both setup guides state the same rule beside the `owner` field.

## Capabilities

### Modified Capabilities
- `keel-chat-slack-bridge`: the session-start notice states the owner-mention rule.

## Impact

`src/core/chat/notice.js`, both setup guides, `scripts/validate_plugin.py`, the published spec, and the changelog. Running sessions see the line at their next session start, `/compact`, or `/clear`.
