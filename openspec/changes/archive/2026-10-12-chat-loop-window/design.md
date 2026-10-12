## Context

Issues #297 and #298 and the owner's decisions of 2026-10-12 recorded on them. Not chosen: judging a loop by message content; exempting the coordinator's groups; flagging mismatched times in message text.

## Facts

- F1 — `pingPongPair` in `src/core/chat/guards.js` checks only that the last `pingpong` (default 8) `message` records alternate between two non-owner roles; it reads no time, and a trip writes a `system` record mentioning `owner` at once (#187, 5.x).
- F2 — In the reported case eight alternations spanned about 2.5 hours, each pair a different issue (#297).
- F3 — A direct group has exactly two members, so the refusal's "any other member's post clears it" names nothing that can happen there.
- F4 — Every record already carries `created` from Keel's clock; times in message text are typed by the session (#298).

## Decisions

- D1 — `limits.pingpong_minutes` in `keel/chat.json` (positive integer, default 10). The guard reads the `message` records after the group's latest record carrying `not_a_loop`; the last `pingpong` of them form a run only if they alternate as before and the first's `created` is within `pingpong_minutes` of now.
- D2 — The group is escalated when, among its records carrying `not_a_loop`, `owner` messages, and `system` records from `keel`, the latest is not an `owner` message. Not escalated: a trip refuses the poster, writes nothing, and the message names `--not-a-loop "<why>"` and says the owner is called if it trips again. A post with `--not-a-loop` is then accepted and stores the reason as `not_a_loop`; with no trip, the option is ignored and nothing is stored. Escalated: a trip writes the `system` record calling `owner` (once, as before), refuses, and does not accept `--not-a-loop`; it says a post by the owner clears it, adding "or another member" only outside a direct group.
- D3 — `--stamp` on `post` and `dm` prefixes `[MM-DD HH:MM] ` in local time, taken from the same clock as the record's `created`.
- D4 — `--help` and `-h` anywhere among `keel chat`'s arguments print the usage and exit 0.
