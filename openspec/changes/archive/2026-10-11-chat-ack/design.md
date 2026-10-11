## Context

Issue #253 and #247, and the #250 split of 2026-10-05.

## Facts

- F1 — `store.readersOf(where, record)` lists roles whose read cursor in the record's group has passed it, and `keel chat show` prints that list.
- F2 — `store.wakes(record, role)` is true for a role a record mentions, a todo's assignee, and the members of a direct group; `@all` is stored as the mention `all`.
- F3 — Readable kinds are `message`, `todo`, and `system`; other kinds (`done`, `edit`, `retract`, `join`, …) are not unread and wake nobody.
- F4 — The bridge posts every pending local record of a mapped group to Slack.

## Decisions

- D1 — `--ack` on `post` and `todo` sets the record field `ack: true`. Its addressed roles are the group's members other than the sender for whom `wakes` is true, plus every other member when it mentions `all` (F2). A record that addresses nobody is refused with `--ack`, naming that it addresses no one.
- D2 — `keel chat ack <id>` writes a record of kind `ack` with `target: <id>` and advances the acknowledger's read cursor past the target. It is refused, by name, for a record that does not ask, for a role it does not address, and for a role that already acknowledged it. A reply from an addressed role to the record also counts as its acknowledgement.
- D3 — `ack` is not a readable kind (F3), so it is never unread and wakes nobody. The bridge does not post it (F4).
- D4 — For a record that asks, `keel chat show <id>` prints three lines, `acknowledged:`, `read, not acknowledged:`, and `not read:`, each over the addressed roles; `--json` carries `acks: {acknowledged, readNotAcknowledged, unread}`. `keel chat acks [--mine]` lists every record in an open group that asks and still waits on an addressed role, with the same three lists; `--mine` keeps those the caller posted.
- D5 — A group view and the wake notice add `(ack requested)` to a record that asks.
