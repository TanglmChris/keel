## Why

On 2026-10-05 the owner asked whether an issue a session mentions in Slack can link to GitHub, so a click opens it. Sessions write `#226` or `TanglmChris/keel#226` in records, and Slack shows both as plain text, so the owner has to look the number up by hand.

## What Changes

- Outbound, outside code, the bridge turns `owner/repo#N` into a Slack link to that repository's issue N. It also turns a bare `#N` into a link to issue N of the project's own GitHub repository, which it reads from the project's `origin` remote.
- A project whose `origin` is not on GitHub gets no links for a bare `#N`. The local record is unchanged.
- Inbound, such a link comes back as the text it showed, so the round trip keeps `#226`.

## Capabilities

### Modified Capabilities
- `keel-chat-slack-bridge`: formatting translation covers issue references.

## Impact

`src/core/chat/mrkdwn.js`, `src/core/chat/bridge.js`, both setup guides, `scripts/validate_plugin.py`, the published spec, and the changelog.
