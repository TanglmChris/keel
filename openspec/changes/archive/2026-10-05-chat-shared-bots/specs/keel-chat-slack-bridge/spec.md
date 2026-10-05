## MODIFIED Requirements

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

When a verified bot's `app:<name>` token is present and the bot serves exactly one role across the projects this machine relays, the bridge MUST open a Socket Mode connection for that bot with the same reconnect, backoff, and pause handling as the shared connection; a bot serving more than one role MUST open none, and status MUST report its direct messages as off with the number of roles it serves. A direct message to a connected bot from a person in `slack.members` MUST become a record from that person's role in the direct group `dm-<a>--<b>` of the two roles, created if absent; a direct message from anyone else MUST be ignored and counted. Records originating on this machine in that direct group MUST be posted to the person's direct-message channel with the bot's token and never to a channel. On every connect the bot's direct-message channels MUST be caught up from the last ts processed.

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

### Requirement: Tokens never enter the repository or a record

The bridge MUST read the app and bot tokens from `KEEL_SLACK_APP_TOKEN` and `KEEL_SLACK_BOT_TOKEN`, or else from the macOS Keychain generic passwords of service `keel-chat-slack`, accounts `app` and `bot`; a registered bot's tokens MUST be read only from that service's accounts `bot:<name>` and `app:<name>`. It MUST NOT write a token to any file, record, status, log, or output; missing tokens MUST fail naming both sources.

#### Scenario: Missing tokens are named, not guessed
- **WHEN** `keel chat bridge run` starts with neither environment variable set and no Keychain entry
- **THEN** it fails naming `KEEL_SLACK_APP_TOKEN` and the Keychain service `keel-chat-slack`
