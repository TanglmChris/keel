## Why

The 5.83 mailbox (#180) is one-to-one and read-once: `send` takes a single `--to`, `read` moves the file away, so two readers of one role race and nobody else ever sees the history. It has no surface for the owner, prints raw UTC stamps, and lives on one machine. Since 2026-10-01 a Claude and a Codex maintenance session run in parallel on this repository, and coordination between them still goes through the owner by hand. The owner wants a work group instead: several roles in one group, `@` one member or `@all`, lightweight todos, maintained membership, several groups and cross-project groups, reachable from another machine and from the phone (issue #187, design frozen with the owner on 2026-10-01).

## What Changes

- **BREAKING (storage, not commands):** the store moves from `<git common dir>/keel-mailbox/` to `<git common dir>/keel-chat/`, an append-only log of immutable records per group plus one read-cursor file per member. 5.83 mail is migrated into two-person groups on first use, and the old directory is renamed, never deleted. `keel mail role | send | list | read` keep working as an alias layer.
- `keel chat` CLI: roles with aliases; groups with membership events, archive, and two-person direct groups; posting with `@role`, `@alias`, and `@all`; replies; todos with an assignee, an optional `issue: #N`, and done records; per-member unread and read receipts; search; edit and retract records; local-time display with `--since` and `--follow`; an auto-maintained Markdown transcript per group.
- Notices: only a mention (or a direct-group message) wakes a Claude session. `@all` and plain messages are counted at the next prompt. A notice lists at most five mentions with relative time. A host-neutral `keel chat notice` prints the same notice for any host, which #183 can reuse. Presence comes from hook heartbeats and a Claude SessionEnd hook.
- Loop guards: a per-role post rate limit and a ping-pong breaker that refuses the next agent post and `@`s the owner.
- `keel chat bridge`: one Slack app and one bridge process per machine, using Socket Mode and the Web API through Node's built-in `WebSocket` and `fetch` (Node 22+ for the bridge only). It relays opted-in projects listed in `~/.keel/chat/projects.json`. It posts only its own machine's roles, with a per-message name and icon, and carries the Keel record in Slack message metadata so other machines rebuild it exactly. Mapping: groups to channels, replies to threads, todo done to ✅, owner mentions to a real Slack mention. Only registered Slack users are relayed. Secrets are redacted before sending. Tokens live in the macOS Keychain or the environment.
- Bridge lifecycle: `install | uninstall | start | stop | pause <duration> | status | run`, as a user LaunchAgent. It catches up after sleep or downtime, restarts when Keel's version changes, and is visible in Login Items, the session-start notice, Slack online and offline posts, and `status`.
- Git archive: on by default for Slack-enabled projects. It writes the store to an orphan `keel-chat` branch with plumbing commits, merges by union, and refuses to push to a public repository unless the project accepts that or names another remote.
- A step-by-step Slack setup guide.

## Capabilities

### New Capabilities

- `keel-chat-slack-bridge`: the per-machine Slack bridge, its mapping and security rules, its lifecycle, and the git archive of the chat store.

### Modified Capabilities

- `keel-cross-host-mailbox`: the one-to-one, read-once mailbox becomes the group chat store and CLI, with mentions, todos, cursors, notices, loop guards, and migration. Messages stay data that gate nothing.
- `keel-native-plugin-package`: the Claude-only hook set gains a SessionEnd presence hook.

## Impact

- **Code:** `src/core/mail.js` becomes `src/core/chat/` (store, CLI, notices, bridge, archive), with `src/core/mail.js` kept as the alias entry. Also `bin/keel.js` (a `chat` dispatch and usage line), `plugins/keel/scripts/mail-hook.js`, and the root `.claude-plugin/plugin.json` hooks.
- **Tests and docs:** new and rewritten validation scenarios in `scripts/validate_plugin.py`, a Python fake Slack server for those scenarios, the resident protocol's hook statement, a setup guide under `docs/`, and `keel/CHANGELOG.md`.
- **Unchanged:** `plugins/keel/hooks/hooks.json`, which Codex also loads.
- **Dependencies:** none added. Keel's engine floor stays `>=20.19.0`; only `keel chat bridge` needs Node 22.
- **Not in scope:**
  - Codex's receiving hooks (#183).
  - Auto-launching offline sessions.
  - A local web page.
  - GitHub Discussions.
  - A menu-bar icon.
