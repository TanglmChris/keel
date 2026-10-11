## Context

Issue #252, and the #250 split of 2026-10-05.

## Facts

- F1 — A record is a front-matter file whose fields follow `FIELD_ORDER` in `src/core/chat/store.js`. Edits and retractions are records of their own whose `target` names the record they change; `view.js` `displayRecords` applies them when showing a group, and only the target's author may make one (`amend`).
- F2 — `store.unread(where, role)` is read by `keel chat unread`, the notice (`notice.js`), the waker (`wake.js`), `keel shift`, and `keel mail`. Each filters or presents what it returns. None depends on its order beyond presenting it.
- F3 — The bridge's `postRecord` already updates an earlier Slack message with `chat.update`, using the posting app's token, for an edit.

## Decisions

- D1 — `--supersedes <id>` is a `post` option. The target must exist in the same group, be a `message` or `todo` by the same author, and be neither retracted nor already superseded; each refusal names why, and when the target is already superseded it names the successor to supersede instead. The new record carries the field `supersedes: <id>` and is otherwise an ordinary message, mentions and wake included.
- D2 — `store.unread` omits any record that a later record in the same group supersedes, whether or not that later record has been read. Every reader of unread records follows (F2), so a superseded record wakes nobody.
- D3 — Order is presentation: `keel chat unread` and the notice list newest first. `store.unread` keeps its order, so its other readers are unchanged.
- D4 — In a group view, a superseded record reads `(superseded by <id>)` and its successor `(supersedes <id>)`.
- D5 — The bridge posts the successor as usual and then updates the superseded record's Slack message, when it has one, to open with `(superseded by <id>)`, with the same token rule as an edit (F3).
