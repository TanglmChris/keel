## Context

Issue #313 and the owner's decision of 2026-10-13 recorded on it. Not chosen: closed issues as a signal; keeping `--shift-at` as an opt-in fallback; a nudge to compact (a model cannot trigger compaction).

## Facts

- F1 — The owner's rule (#313): compact within a continuous task (host auto-compaction at 70 %); change shift when a complete task is finished; `ready --wake` when the next task is already assigned, plain `ready` otherwise.
- F2 — A todo is assigned by `keel chat todo <group> --assignee <role>` and closed by a `done` record targeting it (`keel chat done`, or a reply starting with `done`).
- F3 — 5.121.0's shift nudge reads a host-reported `--context` against `--shift-at` (default 50).

## Decisions

- D1 — For each role considered by `--nudge`, the closed todos assigned to it are the `done` records whose target is a todo with that assignee. The nudge state keeps `closedSeen`, the ids already accounted for; when it is absent, the run records every current closure and nudges nothing.
- D2 — An idle role with a closure not in `closedSeen` and no waiting shift note gets one message, and those closures join `closedSeen`. The message reads `<role>: your task <todo id> ("<first line>") was closed. Change shift at this task boundary: \`keel shift check\`, then …, then clear this session (a session serving Remote Control cannot be cleared: turn it off, clear, then turn it back on).` Here … is ``\`keel shift ready --wake "<note>"\` — you still hold <n> open todo(s)`` when the role has open todos, and ``\`keel shift ready "<note>"\`, and wait for the coordinator to start you with new work`` when it has none. A role that is not idle keeps its closures pending until it is.
- D3 — `--context` and `--shift-at` are refused: `--context and --shift-at were retired in 5.125.0 (#313): a shift follows a task's close, and compaction within a task stays the host's.`
- D4 — `docs/shift-change.md` gains a section stating the policy and the nudge.
