## ADDED Requirements

### Requirement: A role may post as its own Slack app

`keel/chat.json` MAY declare `slack.bots`, a map from a bot's Slack user id to a role. On start the bridge MUST call `auth.test` with each declared role's `bot:<role>` token it finds and treat the role's app as verified only when the returned `user_id` is the declared id; otherwise the role MUST post through the shared app and `keel chat bridge status` MUST name the role and the reason. When Slack answers a verified role's post with `not_in_channel`, the bridge MUST post the record through the shared app under the role's name instead and report the role and channel in status. A declared role with no token on this machine MUST behave as undeclared on it.

#### Scenario: A verified role posts under its own app
- **WHEN** `slack.bots` maps `UBOTRTL` to `rtl`, the Keychain double holds `bot:rtl` whose `auth.test` returns `UBOTRTL`, and `rtl` posts in mapped group `soc`
- **THEN** the fake server receives that `chat.postMessage` with `rtl`'s token and no `username`, while `verify`'s post uses the shared token with `username` `verify`, and an edit of `rtl`'s record calls `chat.update` with `rtl`'s token

#### Scenario: A token for another bot is not used
- **WHEN** `slack.bots` maps `UBOTRTL` to `rtl` but `auth.test` with `bot:rtl` returns `UOTHER`
- **THEN** `rtl`'s post uses the shared token with `username` `rtl`, and `keel chat bridge status --json` reports `rtl` as `mismatch`

#### Scenario: A channel the role's bot is not in falls back
- **WHEN** the fake server answers `rtl`'s token with `not_in_channel` for `CSOC`
- **THEN** the record is posted once through the shared token with `username` `rtl`, and status names `rtl` and `CSOC`

#### Scenario: A mention of a role's bot wakes the role
- **WHEN** the registered owner posts `<@UBOTVERIFY> rerun please` in `CSOC` and `slack.bots` maps `UBOTVERIFY` to `verify`
- **THEN** the imported record mentions `verify` and its text reads `@verify rerun please`

### Requirement: A role's app takes direct messages

When a verified role's `app:<role>` token is present, the bridge MUST open a Socket Mode connection for that app with the same reconnect, backoff, and pause handling as the shared connection. A direct message to it from a person in `slack.members` MUST become a record from that person's role in the direct group `dm-<a>--<b>` of the two roles, created if absent; a direct message from anyone else MUST be ignored and counted. Records originating on this machine in that direct group MUST be posted to the person's direct-message channel with the role's token and never to a channel. On every connect the role's direct-message channels MUST be caught up from the last ts processed.

#### Scenario: The owner messages a session privately
- **WHEN** the fake server pushes, on `rtl`'s app connection, a direct message from `UOWNER` with text `status?`
- **THEN** a record from `owner` appears in `dm-owner--rtl` and `signal/rtl` grows

#### Scenario: The session answers privately
- **WHEN** `rtl` runs `keel chat dm owner "all green"`
- **THEN** the fake server receives one `chat.postMessage` with `rtl`'s token to the channel `conversations.open` returned for `UOWNER`, and no post to a mapped channel carries that text

#### Scenario: A stranger's direct message is ignored
- **WHEN** the fake server pushes, on `rtl`'s app connection, a direct message from an unregistered user
- **THEN** no record is written and the ignored count grows

## MODIFIED Requirements

### Requirement: Outbound posts carry the role and the exact record

For each record that originated on this machine in a group mapped to a channel and not yet posted, the bridge MUST call `chat.postMessage` with the bot token of the sender's verified role app and no `username` or icon, or, when the sender has none, with the shared bot token, `username` set to the role (`<project>/<role>` for a channel mapped by more than one project), and the role's configured icon, in both cases with and `metadata` of `event_type: keel_chat_record` carrying project, id, kind, from, mentions, reply_to, assignee, issue, and target. A reply MUST be posted in its root's thread; a mention of `owner` MUST add a Slack mention of `slack.owner`; text over 3,000 characters MUST be truncated with a pointer to `keel chat show <id>`. A `done` record MUST add a ✅ reaction, `edit` MUST call `chat.update`, and `retract` MUST call `chat.delete`. The posted ts, and the role whose app posted it, MUST be recorded per id so nothing is posted twice and an edit or retraction uses the same app, and a 429 MUST be retried after its `Retry-After`.

#### Scenario: A reply mentioning the owner lands in the thread
- **WHEN** `rtl` posts a message in mapped group `soc`, then replies to it with `@owner done?`
- **THEN** the fake server receives two `chat.postMessage` calls with `username` `rtl` and `keel_chat_record` metadata, the second with `thread_ts` equal to the first's ts and text containing `<@` and the configured owner id

#### Scenario: Rate limiting delays but does not drop
- **WHEN** the fake server answers the first post with 429 and `Retry-After: 1`
- **THEN** the bridge posts the same record again after at least one second, and the record is posted exactly once in the end

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

### Requirement: Tokens never enter the repository or a record

The bridge MUST read the app and bot tokens from `KEEL_SLACK_APP_TOKEN` and `KEEL_SLACK_BOT_TOKEN`, or else from the macOS Keychain generic passwords of service `keel-chat-slack`, accounts `app` and `bot`; a role app's tokens MUST be read only from that service's accounts `bot:<role>` and `app:<role>`. It MUST NOT write a token to any file, record, status, log, or output; missing tokens MUST fail naming both sources.

#### Scenario: Missing tokens are named, not guessed
- **WHEN** `keel chat bridge run` starts with neither environment variable set and no Keychain entry
- **THEN** it fails naming `KEEL_SLACK_APP_TOKEN` and the Keychain service `keel-chat-slack`
