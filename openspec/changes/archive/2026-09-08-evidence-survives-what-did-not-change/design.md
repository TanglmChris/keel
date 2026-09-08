## Context

A contract fingerprint is all-or-nothing by construction, and that is why it is worth trusting. The question this change answers is not how to make it partial, but what the gate should *say* when it moves.

## Goals / Non-Goals

**Goals:**

- An author who can see that a contract change did not touch a check can say so, once, in a place that is recorded.
- The warning then describes what actually needs re-verifying.

**Non-Goals:**

- Making the fingerprint partial, or excluding any field from it. See D1.
- Judging whether the declaration is true. See D3.
- Skipping any completion requirement. Every `M<n>` still needs Evidence, red-green still applies, the Review still runs.

## Decisions

- F1 — The stale-evidence report is already a warning, not a refusal, and its comment states that the gate cannot judge which evidence survives. Basis: `src/core/gates.js`, read 2026-09-08.
- F2 — Issue #112 records four re-verifications in one session from contract changes that could not affect evidence, one of which required breaking and restoring a testbench. Basis: the report.
- D1 — Do not exclude tags from the fingerprint. Basis: `(regression)` is the reporter's own example, and it is precisely the tag that *changes an evidence obligation* — it exempts a check from red-green. Excluding it would let a check be tagged after the fact to escape the requirement, which is the escape hatch 5.50.0 closed from the other side. The fingerprint stays whole; only what the gate says about it changes.
- D2 — The declaration is a flag on the re-record rather than a field in `tasks.md`. Basis: it describes one transition between two contracts, not a property of the task. A field would persist past the transition it is about and would itself be inside the fingerprint, so declaring it would move the anchor it was declaring about.
- D3 — The gate validates that the named checks exist and reports the declaration; it does not verify the claim. Basis: it retains only the previous fingerprint, not the capsule behind it, so it cannot compare a check's old text to its new one — the same limit recorded in issue #115. Stating this in the proposal and the message is what keeps the flag from reading as a verification it is not.
- D4 — `--keep-evidence` without `--record` is refused. Basis: there is no re-record for it to qualify, so accepting it would let an author believe they had declared something that nothing read.
- D5 — A label that is not a check of the new contract is refused, not ignored. Basis: the likeliest cause is a typo or a check that was renamed, and silently ignoring it would leave the author believing evidence was kept that was not.
- D6 — The narrowed warning names both sides: the checks still stale and the checks kept, attributed to the declaration. Basis: a reader of the transcript later — including `keel-review-checklist` — needs to see that the narrowing was declared rather than inferred.

## Hidden Knowledge / Assumptions

- A1 — An author declaring `--keep-evidence` has compared the two contracts themselves. Basis: nothing in the gate can check it, and D3 records why. The declaration's value is that it is explicit and recorded, which is the same value `Discard reason:` has and the same exposure. Durable owner: https://github.com/TanglmChris/keel/issues/112

## Risks / Trade-offs

- The flag can be used to wave away a real contract change. So can a false Reauthorizations note, and the answer is the same: it is visible, it is attributable, and the Review is where it is challenged. What the flag removes is the pressure to write nothing at all, which is what a blanket warning produces once an author decides it overstates.
- One more flag on `task-start`. It appears only with `--record` and is inert otherwise.

## Open Questions

None.
