## Context

Issue #179 sets four priorities: derive mechanical record slots; make re-record recovery accurate without trusting old evidence; remove Keel-owned guidance only where it is duplicated and carries no criterion; and keep the gate/agent split.

## Goals / Non-Goals

**Goals:** a valid task needs no hand-written record slots before `--record`; the review checklist stops restating what `task-complete` already refuses.

**Non-Goals:** filling results, verdicts, or keep reasons; trusting evidence across a contract change; re-splitting skills; model A/B evaluation; changing any gate verdict on a filled record.

## Decisions

- F1 — At 5.83.0, `task-start --record` on an otherwise valid task refuses `record-refused` when Evidence lacks `- Contract:`, and `task-start` with or without `--record` refuses `evidence-label-mismatch` when a declared `M<n>` has no Evidence line. Basis: 2026-10-01 CLI probe on the compact task fixture.
- F2 — The re-record warning already separates checks named by `--keep-evidence` from those still stale and states that Keel records the declaration without verifying it, so item 2 of #179 needs no change. Basis: `taskStart` in `src/core/gates.js`, issue #179's own instruction not to re-implement what exists.
- F3 — No sentence of 60 or more characters appears verbatim in more than one of the six Keel skills, `run-single-task-goal`'s `guidance.md`, and `AGENTS.md`. Two `keel-review-checklist` bullets restate refusals that `task-complete` makes itself: `missing-contract-anchor`/`contract-drift` for the Contract line, and `missing-strategy-evidence` for `.red`/`.green`. Basis: 2026-10-01 scan and `src/core/gates.js`.
- D1 — Slots are derived from the compiled capsule, so a task must first compile apart from its Evidence. Keel adds `Contract` and the bare `M<n>` lines named by the task's own `Verify`/`Commands` labels, recompiles, and, only if that compile passes, adds the strategy-dependent slots. If the final compile does not pass, the file is restored and the result is the ordinary refusal. Basis: #179 item 1, "错误 capsule 仍先拒绝".
- D2 — Every written slot reads `pending`, or `none` for Blocker and Reauthorizations, which are the template's own defaults. Existing lines are never rewritten, so a second run is byte-identical. Basis: #179 completion criteria.
- D3 — Remove only the two restating bullets from the review checklist, and keep their non-mechanical remainder: that evidence-first tasks name their observable proof. Basis: F3 and #179 item 4.

## Hidden Knowledge / Assumptions

None.

## Risks / Trade-offs

- Placeholder slots could look like progress. They read `pending`, which `task-complete` refuses as unfilled, so the gate's verdict on an unrun check does not change.

## Open Questions

None.
