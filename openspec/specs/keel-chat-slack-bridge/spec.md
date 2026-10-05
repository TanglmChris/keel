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

For each record that originated on this machine in a group mapped to a channel and not yet posted, the bridge MUST call `chat.postMessage` with the bot token of the sender's verified role app and no `username` or icon, or, when the sender has none, with the shared bot token, `username` set to the role (`<project>/<role>` for a channel mapped by more than one project), and the role's configured icon, in both cases with and `metadata` of `event_type: keel_chat_record` carrying project, id, kind, from, mentions, reply_to, assignee, issue, and target. A reply MUST be posted in its root's thread; a mention of `owner` MUST add a Slack mention of `slack.owner`; text over 3,000 characters MUST be truncated with a pointer to `keel chat show <id>`. A `done` record MUST add a ✅ reaction, `edit` MUST call `chat.update`, and `retract` MUST call `chat.delete`. The posted ts, and the role whose app posted it, MUST be recorded per id so nothing is posted twice and an edit or retraction uses the same app, and a 429 MUST be retried after its `Retry-After`.

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

The bridge MUST acknowledge every Socket Mode envelope. A channel message carrying `keel_chat_record` metadata MUST be written as that record with `origin: slack` unless that id already exists in the receiving project; metadata absent from the event MUST be fetched with one `conversations.history` call using `include_all_metadata`. A post made by this bridge for a project, through the shared app or a verified role app, MUST NOT be re-imported into that project. A message from a user listed in `slack.members` MUST be imported as that member's role, with `@role`, `@alias`, and `<@U…>` mentions of a person in `slack.members` or a bot in `slack.bots` resolved to roles, appending to the signal of each mentioned role. A message from anyone else MUST be ignored and counted in `status`. A thread reply MUST become `reply_to` its mapped root; `message_changed` MUST become `edit`, `message_deleted` MUST become `retract`, a ✅ reaction from a registered user on a todo MUST become `done`, and a file MUST become a link line without download.

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

### Requirement: A role may post as its own Slack app

A machine MUST list its bots by name in `<KEEL_HOME or ~/.keel>/chat/bots.json`, edited by `keel chat bot add <name>` and `keel chat bot remove <name>`; `keel chat bot list` MUST show whether each bot's Keychain entries exist without printing them. `keel/chat.json` MAY declare `slack.bots`, a map from a bot's Slack user id to a role of that project. On start the bridge MUST call `auth.test` with each listed bot's `bot:<name>` token; a project's role MUST post through a bot only when the project's `slack.bots` maps that bot's returned `user_id` to the role. One bot MAY serve one role in each of several projects; since `slack.bots` is keyed by the bot's id, it serves at most one role per project. A role no verified bot serves MUST post through the shared app. When Slack answers a bot's post with `not_in_channel`, the bridge MUST post the record through the shared app under the role's name instead and report the bot and channel in status. `keel chat bridge status` MUST list each bot with its state, the `<project>/<role>` labels it serves, and its direct-message state.

#### Scenario: A verified role posts under its own app
- **WHEN** bot `rtl` is listed, its Keychain token's `auth.test` returns `UBOTRTL`, `slack.bots` maps `UBOTRTL` to `rtl`, and `rtl` posts in mapped group `soc`
- **THEN** the fake server receives that `chat.postMessage` with the bot's token and no `username`, while `verify`'s post uses the shared token with `username` `verify`, and an edit of `rtl`'s record calls `chat.update` with the bot's token

#### Scenario: A token for another bot is not used
- **WHEN** bot `rtl`'s `auth.test` returns `UOTHER`, which no `slack.bots` maps
- **THEN** `rtl`'s post uses the shared token with `username` `rtl`, and status lists bot `rtl` serving no role

#### Scenario: A channel the role's bot is not in falls back
- **WHEN** the fake server answers the bot's token with `not_in_channel` for `CSOC`
- **THEN** the record is posted once through the shared token with `username` `rtl`, and status names the bot and `CSOC`

#### Scenario: A mention of a role's bot wakes the role
- **WHEN** the registered owner posts `<@UBOTVERIFY> rerun please` in `CSOC` and `slack.bots` maps `UBOTVERIFY` to `verify`
- **THEN** the imported record mentions `verify` and its text reads `@verify rerun please`

#### Scenario: One bot is a different role in each project
- **WHEN** bot `pm` (`UBOTPM`) is listed, project `a` maps `UBOTPM` to `a-pm` with group `ops` on `CA`, project `b` maps it to `b-pm` with group `ops` on `CB`, each role posts, and the owner posts `<@UBOTPM> status?` in `CA`
- **THEN** both posts carry the bot's token, to `CA` and `CB` respectively; `a`'s store gains a record mentioning `a-pm`, `b`'s store gains nothing from it; and status lists bot `pm` serving `a/a-pm` and `b/b-pm`

### Requirement: A role's app takes direct messages

When a verified bot's `app:<name>` token is present and the bot serves exactly one role across the projects this machine relays, the bridge MUST open a Socket Mode connection for that bot with the same reconnect, backoff, and pause handling as the shared connection; a bot serving more than one role MUST open none, and status MUST report its direct messages as off with the number of roles it serves. A direct message to a connected bot from a person in `slack.members` MUST become a record from that person's role in the direct group `dm-<a>--<b>` of the two roles, created if absent; a direct message from anyone else MUST be ignored and counted. Records originating on this machine in that direct group MUST be posted to the person's direct-message channel with the bot's token and never to a channel. On every connect the bot's direct-message channels MUST be caught up from the last ts processed. The shared app MUST take direct messages the same way when a relayed project's `slack.bots` maps the shared app's own bot user id to exactly one role across the relayed projects. It MUST receive them on its existing connection and open no second one, MUST post that role's records as itself, and MUST take none when mapped to more than one role.

#### Scenario: The owner messages a session privately
- **WHEN** the fake server pushes, on `rtl`'s app connection, a direct message from `UOWNER` with text `status?`
- **THEN** a record from `owner` appears in `dm-owner--rtl` and `signal/rtl` grows

#### Scenario: The session answers privately
- **WHEN** `rtl` runs `keel chat dm owner "all green"`
- **THEN** the fake server receives one `chat.postMessage` with `rtl`'s token to the channel `conversations.open` returned for `UOWNER`, and no post to a mapped channel carries that text

#### Scenario: A stranger's direct message is ignored
- **WHEN** the fake server pushes, on `rtl`'s app connection, a direct message from an unregistered user
- **THEN** no record is written and the ignored count grows

#### Scenario: A bot serving two roles takes no direct messages
- **WHEN** bot `pm` with an app token serves `a/a-pm` and `b/b-pm`
- **THEN** no Socket Mode connection is opened with its app token, and status reports its direct messages as off for serving 2 roles

#### Scenario: The shared app takes direct messages for the role it is mapped to
- **WHEN** `rtl`'s `slack.bots` maps the shared app's bot user `UBOT` to `rtl`, and the fake server pushes on the shared connection a direct message from `UOWNER` with text `status?`
- **THEN** it becomes a record from `owner` in `dm-owner--rtl`, `keel chat dm owner` from `rtl` is posted to the owner's direct-message channel with the shared token, no second connection is opened with the shared app token, and status reports the shared app's direct messages as connected

### Requirement: Formatting is translated between Markdown and Slack mrkdwn

Before posting, after redaction and before the length cut, the bridge MUST translate a record's Markdown to Slack mrkdwn: `**x**` and `__x__` to `*x*`, a single `*x*` or `_x_` to `_x_`, `~~x~~` to `~x~`, a heading line to a bold line, a `- `, `* `, or `+ ` list line to a `• ` line, `[text](url)` to `<url|text>`, `owner/repo#N` to a link to that repository's issue N, and a bare `#N` to a link to issue N of the repository the project's `origin` remote names on GitHub (left as text when `origin` is not on GitHub), escaping `&`, `<`, and `>`; text in code spans and fenced code blocks MUST otherwise pass unchanged. Text imported from Slack — a registered person's message or another machine's post — MUST be translated back: `*x*` to `**x**`, `_x_` to `*x*`, `~x~` to `~~x~~`, a GitHub issue or pull-request link showing `#N` or `owner/repo#N` to that text, `<url|text>` to `[text](url)`, `<url>` to `url`, and `&amp;`, `&lt;`, `&gt;` unescaped.

#### Scenario: Markdown is sent as mrkdwn
- **WHEN** `rtl` posts a message containing `**must**`, `*soon*`, `# Plan`, `- item`, `[spec](https://example.com/s)`, `` `a**b` ``, and `x<y&z`
- **THEN** the posted text contains `*must*`, `_soon_`, `*Plan*`, `• item`, `<https://example.com/s|spec>`, `` `a**b` ``, and `x&lt;y&amp;z`, and the local record is unchanged

#### Scenario: A person's mrkdwn is stored as Markdown
- **WHEN** the registered owner sends `*urgent* _today_ ~old~ see <https://example.com|this> a &lt; b`
- **THEN** the imported record's text is `**urgent** *today* ~~old~~ see [this](https://example.com) a < b`

#### Scenario: Issue references link to GitHub
- **WHEN** a project whose `origin` is `git@github.com:acme/rtl.git` posts `see #42, acme/other#7, C# and abc#9`
- **THEN** the posted text contains `<https://github.com/acme/rtl/issues/42|#42>` and `<https://github.com/acme/other/issues/7|acme/other#7>`, leaves `C#` and `abc#9` as text, and the local record is unchanged

#### Scenario: A bare reference stays text without a GitHub origin
- **WHEN** a project with no `origin` remote posts `see #42 and acme/other#7`
- **THEN** the posted text keeps `#42` as text and still links `acme/other#7`

#### Scenario: An issue link comes back as its text
- **WHEN** the registered owner sends `<https://github.com/acme/rtl/issues/42|#42> done`
- **THEN** the imported record's text is `#42 done`

### Requirement: Missed traffic is caught up after downtime

On every (re)connect the bridge MUST page `conversations.history` and `conversations.replies` for each mapped channel from the last ts it processed, import what it missed under the inbound rules, and post every local record still unposted.

#### Scenario: A message sent while the bridge was down arrives
- **WHEN** the bridge is stopped, the fake server's history gains a registered user's message, and the bridge starts again
- **THEN** the message is imported once

### Requirement: Tokens never enter the repository or a record

The bridge MUST read the app and bot tokens from `KEEL_SLACK_APP_TOKEN` and `KEEL_SLACK_BOT_TOKEN`, or else from the macOS Keychain generic passwords of service `keel-chat-slack`, accounts `app` and `bot`; a registered bot's tokens MUST be read only from that service's accounts `bot:<name>` and `app:<name>`. It MUST NOT write a token to any file, record, status, log, or output; missing tokens MUST fail naming both sources.

#### Scenario: Missing tokens are named, not guessed
- **WHEN** `keel chat bridge run` starts with neither environment variable set and no Keychain entry
- **THEN** it fails naming `KEEL_SLACK_APP_TOKEN` and the Keychain service `keel-chat-slack`

### Requirement: The bridge runs unattended but stays visible and controllable

`keel chat bridge install` MUST write a user LaunchAgent plist (`RunAtLoad`, `KeepAlive`, absolute node and CLI paths) and load it with `launchctl`; `uninstall`, `start`, and `stop` MUST unload or load it; `pause <duration>` MUST make the running bridge disconnect and queue until the time passes; `status` MUST report installed, running, connected, paused, served projects, last event, ignored count, and unposted count. `start` MUST retry a bootstrap that fails because an unload is still in progress until it succeeds or a bounded wait ends, MUST fail naming launchctl's output when the service still cannot be loaded, and MUST NOT report success for a failed bootstrap; `stop` and `install` MUST wait, bounded, until launchd has unloaded the service. For a status file written by a bridge launchd started, and where launchd reports the service's state, `status` MUST report the bridge as not running when the service is unloaded or its pid differs from the status file's. The running bridge MUST write its status, post an online notice to mapped channels on start and a stopped notice on clean stop, reconnect with backoff after a disconnect or a `refresh_requested`, and exit so launchd restarts it when Keel's package version changes. For a Slack-enabled project the session-start notice MUST include one bridge status line and, when `slack.owner` is set, one line stating that Slack notifies the owner only for messages that write `@owner`, so a message the owner needs to see or decide on writes it, and that a risk or decision goes in its own message rather than inside a status update.

#### Scenario: Pause queues and resume delivers
- **WHEN** `keel chat bridge pause 2s` runs, `rtl` posts during the pause, and the pause expires
- **THEN** the fake server receives nothing during the pause and the message once afterwards

#### Scenario: Install writes a loadable agent
- **WHEN** `keel chat bridge install` runs with the launchctl and LaunchAgents seams pointed at test doubles
- **THEN** the plist exists with `RunAtLoad`, `KeepAlive`, and `chat bridge run`, and the launchctl double was asked to bootstrap it

#### Scenario: The session learns the bridge is down
- **WHEN** a Slack-enabled project has no running bridge and the SessionStart chat hook runs for a bound role
- **THEN** its notice contains a line stating the bridge is not running

#### Scenario: Start after stop waits for the unload
- **WHEN** a launchctl double fails the first two bootstraps after a bootout with `5: Input/output error`, and `keel chat bridge stop` then `keel chat bridge start` run
- **THEN** `start` exits 0, the double was asked to bootstrap three times, and it reports the service loaded

#### Scenario: A bootstrap that never succeeds is reported
- **WHEN** the launchctl double fails every bootstrap with `5: Input/output error`
- **THEN** `keel chat bridge start` exits non-zero and names launchctl's output

#### Scenario: A stale status file is not reported as running
- **WHEN** a status file written under launchd names a live pid but the launchctl double reports the service unloaded, or loaded with another pid
- **THEN** `keel chat bridge status --json` reports `running: false`

#### Scenario: The session learns to mention the owner
- **WHEN** the SessionStart chat hook runs for a bound role in a Slack-enabled project that names an owner, and again in one whose `keel/chat.json` names none
- **THEN** the first notice contains `@owner` with the rule, including that a risk or decision goes in its own message, and the second does not

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
