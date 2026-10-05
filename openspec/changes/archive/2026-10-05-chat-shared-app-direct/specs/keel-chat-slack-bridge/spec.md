## MODIFIED Requirements

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
