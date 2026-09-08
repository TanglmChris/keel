## Context

A gate's output is read at a stop. Whatever it says is what gets acted on, so a message that is true about the wrong thing is worse than no message, and a message repeated four times crowds out the one that matters.

## Goals / Non-Goals

**Goals:**

- A reference to a check is judged against the checks the task wrote, not against what survived compilation.
- An obligation that can be known when the contract is accepted is stated then.
- A shared explanation appears once per gate run.

**Non-Goals:**

- Ordering problems by causality. See D2.
- Refusing anything new. The red-green statement is a warning, and the label-source change removes a problem rather than adding one.
- Changing what red-green requires, or when it is enforced.

## Decisions

- F1 — Reproduced on 5.52.0. A compact task whose `M2` declaration contains `<experiment_id>` and whose Findings records `Resolved here: M2` reports three problems, the first being `M2 is not a check this task declares`. Removing the slot removes all three. Basis: fixture driven through the real CLI, 2026-09-08.
- F2 — The cause is `commandLabels(task)`, which parses the expanded v3 `Commands` field. A compact v4 task declares `Verify`, so the fallback returns an empty list and every `M<n>` reference is undeclared. Basis: `src/core/gates.js`, read 2026-09-08.
- F3 — The hazard is already documented one branch away: the comment guarding `missing-commands` states that the fallback's empty result "came from the expanded v3 `Commands` field, which a compact task never declares — so their absence is a fact about the fallback, not about the task". Basis: same file.
- F4 — Measured: a two-check `vertical-tdd` task with no red-green Evidence produces four problems in 827 characters, and the sentence `Tag the check \`(regression)\` if it asserts that something already green stays green.` appears four times. Basis: fixture driven through the real CLI, 2026-09-08.
- D1 — Parse the declared labels from the task's own verification form — compact `Verify` first, expanded `Commands` otherwise — and use that wherever a reference is judged. Basis: F2. Label parsing does not depend on a check being concrete, so the labels are available exactly when the compiler's are not, which is the case that misreports.
- D2 — Do not reorder problems by causality. Basis: the reporter offered ordering as an alternative to fixing the derived report, and once the derived report is gone there is nothing to order. A gate that ranked its own diagnostics would need a causality model, and every wrong ranking would be a new version of this defect.
- D3 — The red-green statement is a `task-start` warning, never a refusal. Basis: the obligation belongs to completion and moving the refusal forward would block a task whose author intends to add a `(regression)` tag once the check is written. A warning costs a line and buys the three-plus occurrences this repository and the reporter each paid.
- D4 — A shared explanation is a separate field on the problem, deduplicated by the text renderer only. Basis: the JSON result is consumed by programs that read problems individually, so removing an explanation from some of them would make the payload position-dependent. The repetition is a reading cost, and the reader is the text surface.

## Hidden Knowledge / Assumptions

- A1 — A task's `Verify` labels are parseable even when the block is not concrete. Basis: the label regex matches `M<n>` and an optional tag set, independent of what follows the colon; F1's fixture is the demonstration, since `M2` parses while its check text does not compile. Durable owner: https://github.com/TanglmChris/keel/issues/112

## Risks / Trade-offs

- Judging references against declared labels means a reference to a check whose declaration is malformed now passes that particular test. That is correct: the malformed declaration is reported on its own line, and reporting it twice under two names is the defect.
- One more warning at `task-start`. It appears only for a red-green strategy and names checks rather than restating the rule.

## Open Questions

None.
