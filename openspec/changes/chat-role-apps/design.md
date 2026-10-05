## Context

Issue #187. The owner's choice on 2026-10-05: per-role apps are optional, role by role; roles without one keep the shared app. The two-machine test stays parked.

## Facts

- F1 — The bridge holds one bot token. Every post sets `username` to the role and an optional icon (`postRecord` in `src/core/chat/bridge.js`), and the bridge recognizes its own traffic by one `bot_id` and one `user_id` from `auth.test`.
- F2 — A person's `<@U…>` mention resolves to a role only through `slack.members` (`humanText`), so a mention of any bot user stays raw text and wakes nobody.
- F3 — Direct groups are named `dm-<a>--<b>` with the two roles sorted (`directName` in `src/core/chat/store.js`), and a message in one wakes the other member.
- F4 — The setup guides say "The free plan allows 10 apps, which means 10 machines".
- F5 — The posted map `bridge/posted/<id>.json` already records each record's channel and ts; `chat.update` and `chat.delete` act on a message only for the app that posted it.

## Assumptions

- A1 — Slack: `chat:write.public` lets a bot post in a public channel it has not joined, and a private channel needs an invitation; `message.im` events need `im:history` and go only to the app the message was sent to; `conversations.open` needs `im:write`. Basis: Slack's public scope and event documentation. As with the bridge's other Slack shapes, the fake server models them and a real run is the evidence that Slack agrees.

## Decisions

- D1 — A role's own app is registered in `keel/chat.json` as `slack.bots`, a map from the bot's Slack user id to the role, the same direction as `slack.members`. It is committed so every machine resolves `<@U…>` from a person to that role and treats it as a mention. A role absent from `bots` uses the shared app exactly as before.
- D2 — Its tokens live only in the macOS Keychain, service `keel-chat-slack`, accounts `bot:<role>` and, for direct messages, `app:<role>`, and only on the machine where the role runs. No environment variable: a per-role variable name would have to encode a role name. Tokens stay in memory and never reach a file, record, status, log, or output.
- D3 — At start the bridge calls `auth.test` with each registered role's bot token it finds and uses the token only when the returned `user_id` is the id `bots` declares for that role. A mismatch or a failed call leaves the role on the shared app, and status says why. A token is never used for a role it was not checked against.
- D4 — A record whose sender has a verified app is posted with that app's token, without `username` or icon, since the app's own name and avatar are the point. The posted map records `as: <role>`, and an edit or retraction of that record uses the same token (F5). If Slack answers `not_in_channel`, the record is posted through the shared app as before, and status names the role and channel to invite it to. A role app never blocks the queue.
- D5 — Every verified bot id and bot user id counts as this bridge's own, alongside the shared app's. Own posts are not re-imported into the same project, and own edits, deletions, and reactions are ignored, exactly as for the shared app today.
- D6 — A role whose `app:<role>` token is also present opens its own Socket Mode connection, with the same reconnect, backoff, and pause handling as the shared one. A direct message from a person in `slack.members` becomes a record from that person in the local direct group `dm-<person role>--<role>`, created if absent, so it wakes the role (F3). A direct message from anyone else is ignored and counted. That group's local records are posted to the person's direct-message channel (`conversations.open`) with the role's token and never to a channel. On every connect the role's direct-message channels are caught up from the last ts processed.
- D7 — Direct messages stay on the role's machine. Slack delivers them only to that app (A1), so other machines never see them. The local archive branch carries them like any group.
- D8 — `keel chat bridge status` lists each registered role this machine has a token for, with `verified`, `mismatch`, or `failed`, whether its direct-message connection is up, and the channels it needs inviting to. Roles registered without a local token are not listed: they live on another machine.

## Out of scope

- Converting an agent's `@role` text into a Slack mention of the role's bot. The record keeps the role in its metadata, so rebuilding is exact either way.
- Direct messages between two agents through Slack. Those already work locally as direct groups.
- The two-machine test (#187).
