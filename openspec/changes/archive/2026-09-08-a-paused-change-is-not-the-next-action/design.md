## Context

`keel context` answers one question — what should happen next — and a session's first action follows from it. When that answer is wrong the cost is not effort, it is direction.

## Goals / Non-Goals

**Goals:**

- A person can say "this change is deliberately not the next action" where the change lives.
- Inference honours it and never hides it.
- The declaration is overridable, because a rule that cannot be overridden becomes the next thing to work around.

**Non-Goals:**

- Gating anything on paused state. See D4.
- Automatic pausing — no inference from staleness, from Git, or from a change's age.
- Un-pausing on a schedule. A `since` date is a record, not a timer.

## Decisions

- F1 — `keel context` recommends any active change with an unchecked task, and there is no way to exclude one. The nearest concept, `storageOnly`, is derived from a change having no artifacts rather than declared by a person. Basis: `src/core/context.js`, read 2026-09-08.
- F2 — `.openspec.yaml` tolerates keys OpenSpec does not define: a change directory carrying `status`, `paused_reason`, and `paused_at` still reports `Change 'probe' is valid`. Basis: measured against openspec 1.6.0, 2026-09-08.
- D1 — The declaration lives in the change's own `.openspec.yaml`, under a `keel:` key. Basis: it belongs beside the change rather than in a repository-level list, because the reason is about this change and a list far away rots. It is namespaced because F2 establishes that OpenSpec tolerates the key, not that OpenSpec will never define `status` itself; one nested key costs nothing and settles ownership.
- D2 — A paused change is skipped during inference and named in the result. Basis: this is the `storageOnly` shape, which already reports what it skipped. A silent skip would replace a wrong recommendation with an invisible one, and the reporter's complaint is that Keel's output could not be trusted without a document beside it.
- D3 — When every active change is paused, `context` reports `idle` and lists each reason. Basis: "nothing to do" and "everything here is deliberately on hold" are different states, and the second is the one that tells a returning session whether to un-pause something or start something new.
- D4 — Nothing but inference reads the declaration. `task-start`, `task-complete`, `change-close`, and the guard behave identically on a paused change. Basis: pausing is a statement about priority, and priority is not authority. A paused change whose owner explicitly selects it is being worked on, and a gate that refused it would make the declaration a lock nobody asked for.
- D5 — `keel context --change <paused>` selects it, reporting that it is paused. Basis: D4, and the explicit-selection path already exists for exactly this — the owner has said which change they mean.
- D6 — A malformed or unreadable `keel:` block leaves the change unpaused and warns. Basis: the failure mode of the alternative is a change silently dropped from inference because its config had a typo, which is the defect this change exists to remove, pointed the other way.

## Hidden Knowledge / Assumptions

- A1 — A paused change is paused by a person, and Keel never pauses one itself. Basis: every automatic criterion available — no recent commits, an old `created` date, an unchecked task — describes work that has stalled, which is exactly the state a person most needs to be reminded of. Durable owner: https://github.com/TanglmChris/keel/issues/112

## Risks / Trade-offs

- A paused change is forgotten. Accepted and mitigated by D2 and D3: it is named on every inference that skips it, and an all-paused repository reports each reason. It is more visible paused than it was as a wrong recommendation nobody acted on.
- One more file shape to parse. It is the file OpenSpec already writes per change, and the reader is the scalar parser `context.js` already has for the handoff front matter.

## Open Questions

None.
