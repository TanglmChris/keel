# Design

## Verified facts

- **F1** — `src/core/task-contract.js:811-812` collects question ids with `field(task, "Covers").match(/\bQ\d+\b/g)`, over the whole normalized field including parenthetical prose. Confirmed by reading the live 5.3.6 source.
- **F2** — `src/core/task-contract.js:224-229` reports `missing-command-check` as `${label} must define a concrete public check.` with no token named, while `unfilledToken` exists at `:48` and is already used for `Verify` at `:332`.
- **F3** — `requiredFieldProblems` at `:325-378` treats a task as compact v4 only when `isConcrete(field(task, "Verify"))`. The 5.2.x fix covers `Verify` present-but-tokened; an absent `Verify` still falls through to the ten-field expanded v3 list.
- **F4** — Of that v3 list, `Owner` defaults to `keel-agent` (`:842`), `Mode` defaults to `implementation` (`:263`), `Read` defaults to the base change-artifact set (`:792-800`), `Acceptance` derives from `Covers` (`:847`), and `Report` is consumed nowhere in the capsule. `Candidate Boundary` and `Stop Rules` are owned by `couplingProblems`, which returns `[]` for `Coupling: none` (`:682`).
- **F5** — `loadSelection` at `src/core/gates.js:98` defaults to `tasks.find((task) => !task.checked)` for both `task-start` and `task-complete`.
- **F6** — The documented order is gate-then-checkbox, not checkbox-then-gate: `assets/bootstrap/AGENTS.md:5` ("pass `keel gate task-complete` before checking complete"), `openspec/specs/keel-single-task-goal-execution/spec.md:47` ("`task-complete` passes, and the current agent checks the selected task"), `plugins/keel/skills/keel-run-single-task-goal/SKILL.md:63` ("`keel gate task-complete`, then check the box").
- **F7** — `task-start --record` writes the compiled fingerprint into the task's Evidence `- Contract:` line, and `task-complete` recompiles and compares it (`openspec/specs/keel-core-gates/spec.md:209`, `:170`). A task that has not started therefore holds `Contract: pending`.

## Decisions

### D1 — A `Covers` question reference is the head of an entry, not any substring of it

Match `Q<n>` only where it opens a `Covers` entry, after list punctuation. `- Q1: the open question` still blocks; `- F13 (Q1 resolved -> XHR)` does not.

The alternative the reporter suggested — let `design.md` mark a question resolved and have the gate honour it — was rejected. It makes a deterministic, model-free gate depend on parsing strike-through prose in another file, and it adds a second place where question state lives. The structural rule needs no new authority and no new syntax: authors already write open questions as the subject of a `Covers` entry and resolved ones as supporting detail.

Cost: an author who writes an open question only as trailing detail loses the check. That is the correct trade — a false block that punishes traceability is worse than a missed block on an authoring shape nothing recommends, and `task-start` still refuses the task on its other unresolved authority.

### D2 — `missing-command-check` names the token, like `non-concrete-verify` does

When `isConcrete(check)` is false and `unfilledToken(check)` returns a token, name it. When the check is empty or `none`/`pending`, keep the existing wording, because there is no token to name.

### D3 — Absent `Verify` is a missing field, not a different schema

`Commands` is the field that only an expanded v3 task declares; `Verify` is the compact-v4 equivalent. A task declaring neither has declared no verification at all, so report exactly that, and do not demand the v3 field set it never opted into. This extends the existing spec rule from "declares `Verify` but non-concrete" to "declares no verification form".

### D4 — The expanded v3 required set is the compact set with `Commands` for `Verify`

Required becomes `Covers`, `Commands`, `Evidence` plus the existing boundary check. `Owner`, `Mode`, `Read`, `Acceptance`, `Report`, `Candidate Boundary`, and `Stop Rules` leave the list: the first four have documented defaults the compiler applies anyway (F4), `Report` is consumed nowhere, and the last two are `couplingProblems`' to require when `Coupling: required` (F4).

This is a narrowing of a shipped gate. It cannot admit a task that the compiler could not compile, because every removed field either resolves to a default or is required by another check under the condition that needs it.

### D5 — `task-complete` infers only a task that has started

Given F6, "first unchecked" is the right inference for the documented order and must stay. The hazard is narrower: inferring a task that was never started, then printing its readiness problems under a selection heading the author reads as their own task's failure.

So `task-complete` without `--task` refuses when the inferred task's Evidence `Contract` anchor holds no fingerprint. The refusal names the inferred task, the most recently checked task, and `--task`. `task-start` keeps the plain first-unchecked default, since starting a task that has not started is exactly its job.

This also replaces a confusing failure with an actionable one: such a task would fail `task-complete` on its anchor comparison anyway (F7), just without saying that the selection was a guess.

## Risks

- **R1** — D1 and D4 both narrow refusals. A change that relied on the wide behavior would newly pass. Mitigated by asserting the narrowed boundary from both sides: the shape that must still fail, and the shape that must now pass.
- **R2** — D5 adds a refusal to a passing path. A repo that checks boxes before running the gate, or that skips `--record`, newly needs `--task`. Accepted: that repo is already outside the documented order (F6), and the refusal names the flag.

## Questions

- None.
