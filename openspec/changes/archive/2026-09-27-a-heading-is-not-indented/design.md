## Context

`parseTasks()` (`src/core/task-contract.js`) and `sectionBody()` (`src/core/gates.js`) each carry their
own heading pattern. 5.26.0 made the section's task bound come from the parsed task list so it could not
drift, and left the two heading patterns different on purpose. #160 is the owner of what that left.

## Facts

- **F1** — `parseTasks()` ends a task body at `/^\s*##\s/`; `sectionBody()` ends a section at `/^##\s+/`.
- **F2** — measured on 5.72.0: a tail-position `## Invalidates` whose body has an indented `  ## …` line
  followed by an unclosed `- I2:` refuses `I2`; with `sectionBody()` switched to `/^\s*##\s/` it
  accepts it and reports nothing (the abandoned branch's D5, commit `7bd6448`).
- **F3** — no `tasks.md` under `openspec/` contains a line matching `/^\s+##\s/`, so no archived
  verdict and no pinned fingerprint in the suite moves.
- **F4** — a task field that is absent and has a documented default resolves to the default
  (`keel-task-capsule/v1`), so a field dropped by the task boundary can vanish without a refusal.

## Decisions

- **D1** — a heading is a `##` line at column zero. One predicate, exported from `task-contract.js`
  and used by both readers, so the two cannot diverge again by editing one of them.
- **D2** — the direction is strict, not tolerant: strict drops nothing (an indented line becomes
  field text or section text), while tolerant drops fields silently when they have defaults (F4) and
  drops section entries silently always (F2). Owner's decision, 2026-09-27.
- **D3** — the section half is guarded with a regression check that carries a `Detects:` mutation —
  the tolerant pattern — because the behavior is already correct and has no honest red.

## Alternatives considered

- **A1** — keep both patterns and only add the section guard. Rejected by the owner: it keeps the
  asymmetry where a dropped task field with a default is silent.
- **A2** — make both tolerant. Rejected: that is D5 from the abandoned branch (F2).

## Open questions

None.
