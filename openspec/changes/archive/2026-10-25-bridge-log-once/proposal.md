## Why

Issue #460, scheduled by the owner on 2026-10-25. On this Mac `~/.keel/chat/bridge/bridge.log` had 4431 lines, and most of them were the same two:

- `chat-playground: this repository has no remote`, 2944 times. The bridge syncs each project's chat archive every 10 minutes, and for a repository with no remote the refusal never changes, yet it is logged at every sync.
- `catch-up failed: Slack conversations.open failed: missing_scope (HTTP 200)`, 278 times, once per reconnect. Slack's error response names the missing scope in `needed`, but `SlackError` keeps only `error`, `status`, and `retryAfter`, so the line does not say which scope to add.

A new failure gets lost among thousands of identical lines, and a missing scope has to be found by trial and error.

## What Changes

- **The running bridge logs a repeating failure once.** An archive sync's refusal or error, and a connection's catch-up failure, are logged when they first occur, again only when the message changes, and once more, as a recovery line, when the failure clears.
- **A Slack error names the missing scope.** `SlackError` keeps Slack's `needed` and `provided` fields, and its message reads `missing_scope: needs <scopes>`.
- **A test seam for the archive interval.** `KEEL_CHAT_ARCHIVE_EVERY_MS` overrides the 10-minute sync interval, so a test can watch several syncs.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-chat-slack-bridge`

## Impact

The change touches:
- `src/core/chat/bridge.js` and `src/core/chat/slack.js`;
- `scripts/fake_slack.py`, `scripts/validation/chat.py`, `scripts/validation/registry.py`;
- the published spec and the changelog.

An existing bridge log keeps its old lines; new repeats stop at the bridge's next start on the new version, which launchd triggers by itself when Keel's version changes.
