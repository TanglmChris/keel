## Context

Drift is a hard stop, and a hard stop is where a diagnostic earns its keep: the author cannot proceed, so whatever the message says is what they will act on. This one says a value changed.

## Goals / Non-Goals

**Goals:**

- A reported drift hands the author the set of files whose text the fingerprint covers.
- It states what the fingerprint does not cover, so a reader cannot conclude the wrong thing from silence.

**Non-Goals:**

- Naming the exact field or statement that moved. See D3.
- Changing what the fingerprint covers, when drift is detected, or what it blocks.
- Reading Git. See D4.

## Decisions

- F1 — The message today is two hashes and the selection, with no other content. Basis: `src/core/context.js`, `taskSelection()`, read 2026-09-07.
- F2 — Editing Review `Findings` does not move the fingerprint; editing the text of a `design.md` statement a task's `Covers` cites does. Basis: controlled experiment against the real gates, 2026-09-07, recorded in issue #115.
- F3 — The compiled capsule's authority entries each carry a `source`, such as `openspec/changes/<change>/tasks.md#1.1` or the `design.md` a `D<n>` was resolved from. Basis: read from a real `--json` contract, 2026-09-07.
- F4 — The published spec already states the rule: `keel-task-capsule` says checkbox state, Evidence, Review, Report, comments and whitespace do not drift the contract, while resolved expectation text, mode, scope, Acceptance, verification, stop/autonomy, coupling, defaults version, and prohibitions do. Basis: `openspec/specs/keel-task-capsule/spec.md`. The rule was documented and the diagnostic did not carry it.
- D1 — The drift message names the distinct authority sources, in the order the capsule holds them. Basis: F3 makes them free, and they are precisely the files whose *text* can move this value. A directory listing would not be: `proposal.md` is read for context and contributes no authority text.
- D2 — The message states that Evidence, Review, and the checkbox are not covered. Basis: F2 is the failure this change exists to prevent, and it was a wrong belief rather than a missing file — naming the files alone would not have corrected it, because the author who believes Review is covered sees `tasks.md` in the list and is confirmed.
- D3 — Do not name the field that moved. Basis: the previous capsule is not stored — only its hash is — so the field cannot be computed. Reconstructing one from Git would answer for the last commit rather than for the moment of `task-start`, which are different states whenever a session has been writing, and a message that names the wrong field is worse than one that names a search set.
- D4 — Do not read Git. Basis: D3 removes the reason to, and the gates are local, offline and deterministic; a diagnostic that consults repository history would make the message depend on whether the work had been committed.

## Hidden Knowledge / Assumptions

- A1 — The authority source list is short enough to print. Basis: a capsule's authority entries are its `Covers` citations, and a task citing more than a handful is already over its own scope. If one is ever long the message becomes long with it, which is a cost paid at a hard stop that the author is already reading carefully. Durable owner: https://github.com/TanglmChris/keel/issues/115

## Risks / Trade-offs

- The message grows. It is a hard stop; the previous length was the problem.
- An author may read the source list as exhaustive of *why* rather than of *where*. D2's sentence is what separates the two, which is why it is not optional.

## Open Questions

None.
