## Context

Issue #248 and the owner's decision of 2026-10-11 recorded on it: a per-group `--listen` flag; not tied to `read_only_roles:`, which cannot differ per group.

## Facts

- F1 — Membership is replayed from `join`/`leave` records in `groupState` (`src/core/chat/store.js`); `changeMember` writes them, and `requireOpenMembership` is the check every write by a member passes.
- F2 — `post` (and `todo`, which calls it) is how a role speaks in a group; `ack` and `done` write acknowledgement and closing records.
- F3 — Records are frontmatter files; a field absent from a record reads as absent, so older `join` records need no migration.

## Decisions

- D1 — A `join` record may carry `access: listen`. Replaying the log, a member's latest `join` decides whether it is listen-only; `leave` clears it.
- D2 — A listen-only member stays a member for reading, unread, waking, acknowledging (`ack`), and closing todos assigned to it (`done`, or a `done` reply is a post and therefore refused — `keel chat done <id>` is the way).
- D3 — `post`/`todo` in that group, `group add|remove`, and `group archive` by a listen-only member are refused: `Role <r> is a listen-only member of group <g>: it receives the group but does not post or change it here.`
- D4 — `group list` prints a listen-only member as `<role> (listen)`; `--json` adds `listeners`.
