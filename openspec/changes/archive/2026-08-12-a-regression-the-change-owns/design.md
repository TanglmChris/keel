## Context

F1 — Reproduced against the current tree (2026-08-12, keel 5.38.0): `completionChecks(repo, task, contract)` in `src/core/gates.js:744-792` is the one function both `taskComplete()` and `changeClose()` call to validate a task's `M<n>` Evidence. For a `(regression)`-tagged check it already skips the `.red`/`.green` requirement (lines 768-792, the exemption issue #91's era shipped) but still requires the bare label's Evidence to satisfy nothing more than `isConcrete(evidenceValue(task, label))` (line 759). `isConcrete()` (`src/core/task-contract.js:45-49`) accepts any text that is not empty, `none`, `pending`, or an unfilled `<token>` — so `M4: deferred to C7` already passes this check today, whether or not `C7` means anything, because nothing reads a `C7`.

F2 — The two existing change-level sections, `## Invalidates` (`invalidationProblems`, `gates.js:1000-1100`) and `## Expectation Coverage` (`expectationProblems`, `gates.js:1102-1179`), are both unconditionally required for every change — a change with nothing to declare still writes `- None.`. Both are located by heading and bounded by the shared `sectionBody()` helper (`gates.js:974-987`, fixed by issue #71/#75 to stop at the next `##` heading or the next task, whichever comes first).

F3 — The closest existing *conditional* field is `Coupling`: a task's `Coupled Iteration Contract` fields are required only `WHEN Coupling: required` (`couplingProblems`, `src/core/task-contract.js:802-865`; `openspec/specs/keel-task-capsule/spec.md:63-67`). That contract is scoped to one task regenerating candidate artifacts, not to a check shared across several tasks in one change — it is not a fit for this issue's ask, but its conditional shape (absent by default, required once a trigger fires) is the shape this change reuses at the change level.

## Goals / Non-Goals

**Goals:**
- Give a `(regression)`-tagged check exactly one place to point when its assertion — something already proven stays true — only needs to run once for the whole change, instead of once per task.
- Make that deferral structurally checked (the referenced check must exist and, by close, have run) rather than trusted prose.

**Non-Goals:**
- Touching `src/core/task-contract.js`'s compiled capsule or fingerprint. The deferral is an Evidence-time fact, not a compile-time one; the `(regression)` tag already compiles into the capsule (issue #91's work) and this change reads that flag rather than re-deriving it.
- Letting a non-`(regression)` check defer. A deferred check has no red by construction; a task's own behavior check must keep one, per the existing `regression-only-strategy` rule this change does not touch.
- Requiring `## Change Verify` / `## Change Evidence` from every change. Most changes have no once-per-change check; the sections are required only once some task's Evidence actually defers to one.
- A change-level Review. `## Change Evidence`'s claims are held to the same current-agent honesty norm every other Evidence value already is; this change adds no second review surface.

## Decisions

D1 — `## Change Verify` and `## Change Evidence` are parsed the same way `## Invalidates`/`## Expectation Coverage` already are: located by heading, bounded by the existing `sectionBody()` helper, unchanged. Basis: reuses a boundary rule this repo already fixed once (F2) instead of writing a second one that could drift from it.

D2 — The trigger for requiring `## Change Verify` is reference, not declaration: if no task's Evidence defers to a `C<n>`, both sections may be absent and `change-close` reports nothing about them. The first task whose Evidence reads `deferred to C<n>` is what makes the section's absence — or that label's absence from it — a problem. Basis: mirrors `couplingProblems`'s conditional-on-use shape (F3) rather than `## Invalidates`'s unconditional one; requiring an empty section from every change would be the same boilerplate #71/#75 already removed the equivalent of.

D3 — Only a `(regression)`-tagged `M<n>` may defer. `completionChecks` reads the tag directly from the compiled contract (`contract.capsule.verification.commands[].regression`, already present per F1) rather than re-deriving it from the task's raw text, so this cannot disagree with what the `(regression)` tag itself already decided. An untagged check whose Evidence reads `deferred to C<n>` fails with a diagnostic naming the check and the reason, distinct from a plain missing-evidence failure.

D4 — Resolution is two-phase, matching when each fact is knowable:
  - `task-complete` (per task, as soon as that task's own Evidence is written) checks only that the referenced `C<n>` is *declared* in `## Change Verify` — not that it has already run, because at that point it legitimately may not have.
  - `change-close` (once, after every task in the change is checked complete) checks that every *referenced* `C<n>` carries concrete `## Change Evidence`, and that `## Change Verify`'s own labels are well-formed (contiguous, ordered from `C1`, each check concrete) — the same shape `commandLabelProblems` already enforces for `M<n>`, applied to `C<n>`.
  A task is never blocked on a change-wide check the change has not reached yet; the change cannot close until that check is answered.

D5 — Diagnostic codes, each naming exactly one missing piece:
  - `deferred-evidence-not-regression` — an untagged check's Evidence defers.
  - `deferred-check-unresolved` — defers to a `C<n>` that `## Change Verify` does not declare, whether because the label is absent from an existing section or the section does not exist at all; the same message covers both, since from the deferring task's side both read as "not declared."
  - `change-verify-shape` — the section exists but its `C<n>` labels are non-contiguous, duplicated, or a check is non-concrete.
  - `change-evidence-missing` — a declared `C<n>` has no concrete `## Change Evidence` by close.
  Four codes, not five: an earlier draft gave "section absent" its own code, but `completionChecks` already runs per task inside both `task-complete` and `change-close`, so the absent-section case surfaces through the same resolution check as the label-not-found case rather than needing a second one. Basis: this file's own stated rule that a diagnostic names the field to add rather than describing the authority abstractly.

D6 — `deferred to C<n>` is recognized by matching the front of the bare Evidence value (`/^deferred to (C[1-9]\d*)\b/i`), not by scanning the whole value for the phrase. Basis: matches how the front of a bare Evidence value is already read elsewhere in this file (e.g. `Resolved here:`/`Durable owner:` prefixes in Review Findings), so a check that happens to mention "deferred" mid-sentence in its own real result is not misread as a deferral.

## Hidden Knowledge / Assumptions

None — the two changed gates (`task-complete`, `change-close`) and every input they read are cited directly from `src/core/gates.js` above (F1-F3).

## Risks / Trade-offs

- A change could declare a `C<n>` no task ever references. This is not refused: an author may reasonably declare the change-level check before writing the task that will defer to it. The cost is an unused declaration, not a silent hole — `change-close` still requires concrete `## Change Evidence` for every *declared* `C<n>` regardless of whether anything defers to it, so an orphan declaration cannot vanish unnoticed either.
- The front-anchored `deferred to C<n>` match (D6) means an Evidence value that happens to start with those exact words for an unrelated reason would be read as a deferral. This is the same class of trade-off the `(regression)` tag and `Resolved here:`/`Durable owner:` prefixes already accept for their own keyword matching, and it fails toward a visible diagnostic (unresolved or wrong-tag) rather than a silent pass.

## Open Questions

None.
