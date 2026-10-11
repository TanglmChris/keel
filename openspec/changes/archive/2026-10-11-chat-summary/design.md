## Context

Issue #255, and the #250 split of 2026-10-05. It builds on #252 (`--supersedes`, 5.101.0) and #253 (acknowledgements).

## Facts

- F1 — `keel chat <group> --since <90s|15m|2h|3d|date>` already parses a time with `view.js` `parseSince`, and a group view advances the viewer's read cursor unless `--peek` is given.
- F2 — Todos close by a `done` record or a reply opening `done`; `store.openTodos` lists the open ones.
- F3 — `store.ackStatus(where, record)` splits a record's addressed roles into acknowledged, read without acknowledging, and not read, and `store.openAcks` lists records still waiting.
- F4 — The owner role reads every group; any other role reads the open groups it belongs to.

## Decisions

- D1 — `keel chat summary --since <time>` requires `--since`, parsed as F1 parses it, and refuses a missing or unreadable value by name. `--group <g>` limits it to one group. It covers the groups the caller can read (F4); a worktree with no role is refused, naming `keel chat role --set`.
- D2 — Per group with anything since the time, it lists per sender, in role order: the number of messages; each todo opened since then with its assignee and `open` or `done`; each todo closed since then, whenever opened; and each record that supersedes another, named with what it superseded. A superseded record is not listed on its own.
- D3 — After the groups, it lists every record in those groups that asks for an acknowledgement, posted since the time and still waiting, with the roles that have not acknowledged it (F3).
- D4 — It reads with peek semantics: no read cursor moves. `--json` prints `{since, groups: [{group, senders: [{role, messages, todosOpened, todosClosed, supersedes}]}], waitingAcks: [...]}`.
- D5 — With nothing since the time, it prints one line saying so and exits 0.
