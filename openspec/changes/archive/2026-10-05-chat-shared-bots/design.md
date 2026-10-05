## Context

Issue #187. Owner decisions on 2026-10-05: bots are named generically (PM, Spec, Verify, Design, Flow, Report, Review); one bot appears as a different role in each project's channel; a bot serving several roles takes no direct messages for now.

## Facts

- F1 — 5.93.0 reads a role app's token from the Keychain account `bot:<role>` and verifies it against `slack.bots` (`verifyRoles` in `src/core/chat/bridge.js`), so one token can serve only the role it is named after.
- F2 — `slack.bots` lives in each project's own `keel/chat.json` and maps a bot user id to a role, so a mapping is already scoped to the project and its channels.
- F3 — A direct message carries no channel of a project, so nothing in it says which project's role it is for.
- F4 — The free plan allows 10 apps; the owner's plan is one shared app per machine plus seven bots.

## Decisions

- D1 — A machine lists its bots by name in `<KEEL_HOME>/chat/bots.json`, edited by `keel chat bot add <name>` and `keel chat bot remove <name>`; `keel chat bot list` shows each with whether its `bot:<name>` and `app:<name>` Keychain entries exist, never their values. The list holds names only.
- D2 — On start the bridge calls `auth.test` with each listed bot's token. A project's role speaks through a bot when the project's `slack.bots` maps that bot's returned user id to the role (F2). The same bot may serve one role in each of several projects, and at most one per project, because `slack.bots` is keyed by the bot's id. A listed bot whose token is missing or fails `auth.test` serves nothing, and status says why.
- D3 — Posting, editing, the `not_in_channel` fallback, mention resolution, and recognizing the bridge's own traffic work as in 5.93.0, keyed by the bot that serves the role.
- D4 — A bot with an `app:<name>` token opens its direct-message connection only when it serves exactly one role across the projects this machine relays, because a direct message cannot say which project it is for (F3). Otherwise no connection is opened, and status reports the bot's direct messages as off with the number of roles it serves.
- D5 — Status lists bots, not roles: name, state (`verified` or `failed`), reason, the `<project>/<role>` labels it serves, whether its direct messages are connected or why they are off, and the channels to invite it to.
- D6 — 5.93.0's per-role Keychain accounts are the same `bot:<name>` form, so an entry stored for a role keeps working once that name is listed with `keel chat bot add`. The `mismatch` state is gone: a bot whose user id no project maps simply serves nothing.
