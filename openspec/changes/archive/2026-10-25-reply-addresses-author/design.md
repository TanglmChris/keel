## Facts

- F1 — `post()` (`src/core/chat/store.js`) sets `mentions` only from the text, through `resolveMentions`. `--reply-to` sets `reply_to`, and after the write it only advances the replier's cursor and closes a todo (#201, D6).
- F2 — Every "addressed" decision reads the record's own fields through `wakes(record, role)`: mentions, a todo's assignee, and direct-group members. That covers the notice, `notice --check`, the hooks' signal files (`signalTargets`), the tick's waker, the patrol, and `addressedRoles` for acknowledgements.
- F3 — The 2026-10-25 kaiwu-ip records differ only in that: `20261025T122657098Z-kaiwu-verify-iecc-43ba77` has `reply_to` and no `mentions`, and the 19:50 reply has `mentions: [kaiwu-pm-iecc]` (#468).

## Decisions

- D1 — The reply's author is added to `mentions` when the record is written. `wakes` is not taught to look up `reply_to` at read time. Writing it into the record reaches every reader in F2 at once, keeps `wakes` a function of the record alone, and is honored by older Keel versions reading the same store.
- D2 — The answered role is added only when it differs from the replier, is a member of the group, and is not already mentioned. A sender that is not a member, such as Keel's own notices, is never woken by a reply.
- D3 — The mention is computed before the `--ack` check, so a reply with `--ack` and no `@` addresses the answered role and is accepted.
