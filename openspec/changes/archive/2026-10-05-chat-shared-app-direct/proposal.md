## Why

On 2026-10-05 the owner asked the Keel maintenance session to message them directly in Slack. Every role now has a bot of its own, so the owner decided that the shared app (my-keel-bot) becomes that session's identity. Keel lets only a registered bot take direct messages. The shared app, which carries every project's channels, cannot, even when it would serve exactly one role.

## What Changes

- A project's `slack.bots` may map the shared app's own bot user to a role. When exactly one role across the relayed projects is mapped that way, the shared app takes direct messages for that role, on its existing Socket Mode connection, and posts that role's records as itself.
- Status lists the shared app's direct-message state beside the registered bots.
- The setup guides say how, including the scopes direct messages need (`im:history`, `im:write`, the Messages tab, and the `message.im` event).

## Capabilities

### Modified Capabilities
- `keel-chat-slack-bridge`: the shared app may take direct messages for one role.

## Impact

`src/core/chat/bridge.js`, `src/core/chat/cli.js`, both setup guides, `scripts/validate_plugin.py`, the published spec, and the changelog.
