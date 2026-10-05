## Why

Issue #187, follow-up to 5.93.0 on the same day. 5.93.0 tied a Slack app to one role: its token is stored as `bot:<role>`. The free plan allows 10 apps, the owner runs several projects, and every project has its own PM, spec, and so on. The owner wants a small set of bots named for what they are in Slack — PM, Spec, Verify, Design, Flow, Report, Review — each appearing as that project's role in each project's channel, so the visible identity is the bot and the role behind it is whichever session the channel's project assigns.

## What Changes

- A bot is registered once per machine by name, `keel chat bot add <name>`, with its tokens in the Keychain as `bot:<name>` and `app:<name>`.
- `keel/chat.json` `slack.bots` keeps its form, a bot user id mapped to a role, and now means "this project's role speaks through this bot". The same bot may map to a different role in each project. Because the map is keyed by the bot's id, a bot serves at most one role per project.
- A bot's direct messages work only while it serves exactly one role across the projects this machine relays; a bot serving several roles opens no direct-message connection, and status says so.
- `keel chat bridge status` lists bots, with the roles each serves, instead of roles.

## Capabilities

### Modified Capabilities
- `keel-chat-slack-bridge`: role apps become registered bots shared across projects; direct messages need a bot serving one role.

## Impact

`src/core/chat/{bridge,cli,lifecycle}.js`, `scripts/validate_plugin.py`, both Slack setup guides, both READMEs, the published spec, and the changelog. A 5.93.0 Keychain entry `bot:<role>` keeps working once that name is registered with `keel chat bot add <role>`.
