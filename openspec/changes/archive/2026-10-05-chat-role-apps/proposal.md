## Why

Issue #187, item parked on 2026-10-03 and taken up on 2026-10-05: in Slack every role on a machine speaks through that machine's one keel app, which only swaps the display name. The owner can tell who wrote a message, but cannot `@` a session the way Slack mentions work, cannot message one privately, and does not see the sessions in the member list. The owner chose to let each role optionally have its own Slack app, and keep the shared app for every role that does not.

## What Changes

- `keel/chat.json` `slack.bots` registers a role's own app by its bot user id, the way `slack.members` registers people. A registered bot mention (`<@U…>`) from a person resolves to that role on every machine.
- On the machine where the role runs, the bridge reads that role's bot token from the Keychain (`keel-chat-slack`, account `bot:<role>`), checks with `auth.test` that it belongs to the registered bot, and posts the role's records under the app's own identity. A role without a verified app posts through the shared app as before; a channel the role's bot cannot post in falls back to the shared app and is reported.
- With an app-level token too (`app:<role>`), the role's app opens its own Socket Mode connection, and a direct message from a registered person becomes a record in the local direct group `dm-<person>--<role>`; the role's replies there go back as direct messages.
- `keel chat bridge status` reports each role app's state.
- The Slack setup guide adds an optional per-role section and corrects "10 apps means 10 machines".

## Capabilities

### Modified Capabilities
- `keel-chat-slack-bridge`: outbound posts may go out under a role's own app; tokens gain per-role Keychain accounts; registered bot mentions resolve to roles; role apps take direct messages.

## Impact

`src/core/chat/bridge.js`, `src/core/chat/config.js`, `src/core/chat/lifecycle.js`, `src/core/chat/cli.js`, `scripts/fake_slack.py`, `scripts/validate_plugin.py`, both Slack setup guides, both READMEs, the published spec, and the changelog. The two-machine test stays parked on #187.
