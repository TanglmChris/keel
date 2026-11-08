## Facts

- F1 — `wakes(record, role)` in `src/core/chat/store.js` is the single question every waker asks: `signalTargets` (the signal files), `notice.check` and the file-changed hook, `keel tick`'s resume of ended sessions, the wake candidates in `cli.js`, and drift. A record that answers false there wakes no one anywhere.
- F2 — A record is a markdown file with front matter written by `renderRecord` from `FIELD_ORDER`; `parseRecord` reads scalars as strings, so a boolean is stored as text.
- F3 — `post(where, options)` builds the record; `directPost` calls it for `keel chat dm`; `keel chat <group> <text>` and `post` share it. `--ack` is validated in `post`.
- F4 — The mailbox spec says a record appends to `signal/<role>` only when it mentions the role, assigns a todo or is in its direct group; that is a necessary condition, so a further reason not to wake does not contradict it.

## Decisions

- D1 — A record field `no_wake: yes`, added to `FIELD_ORDER`; `wakes()` returns false first when it is present. No other consumer needs a change (F1).
- D2 — `post` takes `options.noWake`; `directPost` passes `extra.noWake`; the CLI switch is `--no-wake` on `post`, `dm` and the `<group> <text>` form.
- D3 — `--no-wake` with `--ack` is a `ChatError` naming both (F3).
- D4 — The record's readers are unchanged: unread, show, search, the Slack bridge. A no-wake record is still a message.
- D5 — Default unchanged for every machine sender (`keel lock`, shift), by the owner's answer.
