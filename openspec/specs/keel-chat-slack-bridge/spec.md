## Purpose

Define the per-machine Slack bridge that carries a repository's group chat to sessions on other machines and to the owner's phone: which projects it serves, how records go out and come in, the redaction and registration rules that keep secrets in and strangers out, where its tokens live, how it runs unattended yet stays visible and controllable, and the orphan-branch archive that keeps the history beyond Slack's retention.

## Requirements

### Requirement: One bridge per machine relays opted-in projects

`keel chat bridge run` MUST serve every project listed in `<KEEL_HOME or ~/.keel>/chat/projects.json` whose `keel/chat.json` declares `slack.enabled: true`, and no other. `keel chat bridge add [repo]` and `remove [repo]` MUST edit that list, which holds paths only. The bridge MUST connect through Slack Socket Mode with an app-level token and call the Web API with a bot token, using only Node's built-in `WebSocket` and `fetch`; on a Node without `WebSocket` every `bridge` command except `status` MUST fail naming Node 22. The local store MUST remain the only source of truth: agents use `keel chat`, never Slack.

#### Scenario: A project without opt-in is not relayed
- **WHEN** two projects are listed, only one declares `slack.enabled: true`, and both post a message
- **THEN** the fake Slack server receives exactly the opted-in project's message

#### Scenario: An old Node is told what it needs
- **WHEN** `keel chat bridge run` starts where `globalThis.WebSocket` is undefined
- **THEN** it exits non-zero with a message naming Node 22

### Requirement: Outbound posts carry the role and the exact record

For each record that originated on this machine in a group mapped to a channel and not yet posted, the bridge MUST call `chat.postMessage` with `username` set to the role (`<project>/<role>` for a channel mapped by more than one project), the role's configured icon, and `metadata` of `event_type: keel_chat_record` carrying project, id, kind, from, mentions, reply_to, assignee, issue, and target. A reply MUST be posted in its root's thread; a mention of `owner` MUST add a Slack mention of `slack.owner`; text over 3,000 characters MUST be truncated with a pointer to `keel chat show <id>`. A `done` record MUST add a ✅ reaction, `edit` MUST call `chat.update`, and `retract` MUST call `chat.delete`. The posted ts MUST be recorded per id so nothing is posted twice, and a 429 MUST be retried after its `Retry-After`.

#### Scenario: A reply mentioning the owner lands in the thread
- **WHEN** `rtl` posts a message in mapped group `soc`, then replies to it with `@owner done?`
- **THEN** the fake server receives two `chat.postMessage` calls with `username` `rtl` and `keel_chat_record` metadata, the second with `thread_ts` equal to the first's ts and text containing `<@` and the configured owner id

#### Scenario: Rate limiting delays but does not drop
- **WHEN** the fake server answers the first post with 429 and `Retry-After: 1`
- **THEN** the bridge posts the same record again after at least one second, and the record is posted exactly once in the end

### Requirement: Secrets are redacted before anything leaves the machine

Before sending any text to Slack the bridge MUST replace Slack tokens, GitHub tokens (`ghp_`, `github_pat_`), `sk-` API keys, AWS access key ids, PEM private-key blocks, and `password|token|secret` assignments with `[redacted]`; the local record MUST keep its original text.

#### Scenario: A token in a message is not sent
- **WHEN** a message body contains `xoxb-123-456-abcdef`
- **THEN** the text the fake server receives contains `[redacted]` and not `xoxb-123`, and the local record still contains it

### Requirement: Inbound messages are imported only from registered people and Keel posts

The bridge MUST acknowledge every Socket Mode envelope. A channel message carrying `keel_chat_record` metadata MUST be written as that record with `origin: slack` unless that id already exists in the receiving project; metadata absent from the event MUST be fetched with one `conversations.history` call using `include_all_metadata`. A post made by this bridge for a project MUST NOT be re-imported into that project. A message from a user listed in `slack.members` MUST be imported as that member's role, with `@role`, `@alias`, and `<@U…>` mentions resolved to roles, appending to the signal of each mentioned role. A message from anyone else MUST be ignored and counted in `status`. A thread reply MUST become `reply_to` its mapped root; `message_changed` MUST become `edit`, `message_deleted` MUST become `retract`, a ✅ reaction from a registered user on a todo MUST become `done`, and a file MUST become a link line without download.

#### Scenario: The owner's phone message wakes the mentioned session
- **WHEN** the fake server pushes a message from the registered owner in the `soc` channel with text `@verify rerun please`
- **THEN** a `message` record from `owner` mentioning `verify` appears in `soc`, and `signal/verify` grows

#### Scenario: A stranger cannot reach an agent
- **WHEN** the fake server pushes a message from an unregistered user mentioning `@verify`
- **THEN** no record is written, `signal/verify` is unchanged, and `keel chat bridge status --json` counts one ignored message

#### Scenario: Another machine's post is rebuilt exactly
- **WHEN** the fake server pushes a bot message whose metadata carries a record id, sender `codex-maint`, and mentions `verify`
- **THEN** the record is written with that id, sender, and mentions, and pushing the same event again writes nothing

#### Scenario: Two projects sharing a channel both receive
- **WHEN** projects `a` and `b` on one machine both map group `ops` to the same channel and `a`'s `rtl` posts
- **THEN** the message is posted once with `username` `a/rtl`, and `b`'s store gains the record with sender `a/rtl`

### Requirement: Missed traffic is caught up after downtime

On every (re)connect the bridge MUST page `conversations.history` and `conversations.replies` for each mapped channel from the last ts it processed, import what it missed under the inbound rules, and post every local record still unposted.

#### Scenario: A message sent while the bridge was down arrives
- **WHEN** the bridge is stopped, the fake server's history gains a registered user's message, and the bridge starts again
- **THEN** the message is imported once

### Requirement: Tokens never enter the repository or a record

The bridge MUST read the app and bot tokens from `KEEL_SLACK_APP_TOKEN` and `KEEL_SLACK_BOT_TOKEN`, or else from the macOS Keychain generic passwords of service `keel-chat-slack`, accounts `app` and `bot`. It MUST NOT write a token to any file, record, status, log, or output; missing tokens MUST fail naming both sources.

#### Scenario: Missing tokens are named, not guessed
- **WHEN** `keel chat bridge run` starts with neither environment variable set and no Keychain entry
- **THEN** it fails naming `KEEL_SLACK_APP_TOKEN` and the Keychain service `keel-chat-slack`

### Requirement: The bridge runs unattended but stays visible and controllable

`keel chat bridge install` MUST write a user LaunchAgent plist (`RunAtLoad`, `KeepAlive`, absolute node and CLI paths) and load it with `launchctl`; `uninstall`, `start`, and `stop` MUST unload or load it; `pause <duration>` MUST make the running bridge disconnect and queue until the time passes; `status` MUST report installed, running, connected, paused, served projects, last event, ignored count, and unposted count. The running bridge MUST write its status, post an online notice to mapped channels on start and a stopped notice on clean stop, reconnect with backoff after a disconnect or a `refresh_requested`, and exit so launchd restarts it when Keel's package version changes. For a Slack-enabled project the session-start notice MUST include one bridge status line.

#### Scenario: Pause queues and resume delivers
- **WHEN** `keel chat bridge pause 2s` runs, `rtl` posts during the pause, and the pause expires
- **THEN** the fake server receives nothing during the pause and the message once afterwards

#### Scenario: Install writes a loadable agent
- **WHEN** `keel chat bridge install` runs with the launchctl and LaunchAgents seams pointed at test doubles
- **THEN** the plist exists with `RunAtLoad`, `KeepAlive`, and `chat bridge run`, and the launchctl double was asked to bootstrap it

#### Scenario: The session learns the bridge is down
- **WHEN** a Slack-enabled project has no running bridge and the SessionStart chat hook runs for a bound role
- **THEN** its notice contains a line stating the bridge is not running

### Requirement: The chat store is archived to an orphan branch without exposing it publicly

`keel chat archive sync` MUST commit the synced layer of the store (records, cursors, members, presence) to `refs/heads/keel-chat` using git plumbing, without touching the worktree or the index, merging a fetched remote branch by union of paths. It MUST push only when `archive.remote` is declared, `archive_public: accept` is declared, or the repository is known to be private; otherwise it MUST commit locally and report the refused push naming those options. `keel chat archive pull` MUST import records missing locally. Archive MUST default on for Slack-enabled projects, and the running bridge MUST sync periodically.

#### Scenario: Archive leaves the worktree alone
- **WHEN** `keel chat archive sync` runs in a repository with a dirty worktree
- **THEN** `refs/heads/keel-chat` contains the group's record files, and `git status --porcelain` is unchanged

#### Scenario: A public repository is not pushed
- **WHEN** visibility is reported public and neither `archive.remote` nor `archive_public` is declared
- **THEN** the local branch is updated, no push runs, and the output names `archive_public` and `archive.remote`

#### Scenario: A second machine restores history
- **WHEN** a clone fetches `keel-chat` and runs `keel chat archive pull`
- **THEN** `keel chat soc --peek` shows the archived messages
