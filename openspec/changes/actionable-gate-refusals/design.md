## Context

Both defects are DX consequences of gates added in 5.2.4 and 5.3.3. Neither is a correctness bug in what the gates verify; both are cases where the refusal is broader than the rule it enforces, and where the message does not carry the rule.

`SHARED_DURABLE_OWNER_FORMS` (`src/core/gates.js:258`) is documented as a *shape* check, with the comment stating plainly that gates run without network and have never confirmed an archive path resolves either. That is the argument that undoes the current boundary: if the accepted forms are unverified shapes, then refusing a repo-relative path — the one form a gate *can* check — is the least defensible line to draw.

The red-green requirement (`src/core/gates.js:437-449`) applies per `M<n>` with no way to say that one check is a guard rather than a slice. The `(fast)`/`(full)` layer tag added in 5.2.2 already established both the syntax and the fingerprint discipline for per-check annotations.

## Goals / Non-Goals

**Goals:**
- An honest regression check can stand as its own `M<n>`.
- A durable owner can be a file the repository actually keeps.
- Every refusal names what it would accept.

**Non-Goals:**
- Per-check strategies (#21's option 2). Rejected as larger than the problem: it restructures the capsule's verification shape and forces every existing task through a migration, to express something one tag expresses.
- Judging whether an owner is a *good* owner. That stays Review.
- Relaxing what `keel/HANDOFF.md` may be. It remains refused everywhere.

## Decisions

- **F1** — The owner whitelist is `openspec/changes/…` (tested separately at both call sites), plus `keel/archive/…` or `https?://` via `SHARED_DURABLE_OWNER_FORMS`. Basis: `src/core/gates.js:258-259`, `:610-613`, `:685-688`. Three call sites share it: Review `Findings`, `## Expectation Coverage`, `## Invalidates`.
- **F2** — `invalidationProblems` and `expectationProblems` take `(content, tasks)` and have no `repo`. Basis: `src/core/gates.js:559`, `:646`. Both call sites (`taskStart`, `changeClose`) do have `repo`, so threading it is mechanical.
- **F3** — The `(fast)`/`(full)` layer tag parses in `verification()` at `src/core/task-contract.js:161` and is emitted into the capsule only when it is not the default. Basis: `:806-813`. Untagged checks therefore compile byte-identically, which is what kept 5.2.2 from moving any fingerprint.
- **D1** — A durable owner may be any repo-relative path that **exists**. Basis: the user's decision, and F1's own comment: an existence check is strictly more verification than the forms already accepted. A nonexistent path is still refused, which is a new refusal the old whitelist could not make for `keel/archive/…`.
- **D2** — `keel/HANDOFF.md` stays refused even though it exists. Basis: it is a pointer override by protocol definition, not a durable owner; existence is necessary, not sufficient.
- **D3** — Regression exemption is a per-check tag, `M2 (regression): …`, reusing F3's mechanism and emission rule. Basis: the user's decision. The tag lands in the capsule and therefore in the fingerprint, so the exemption is a declared part of the contract that Review sees, not a silent skip.
- **D4** — A red-green strategy MUST retain at least one untagged check. Basis: without it, `Strategy: vertical-tdd` with every check tagged is vertical-tdd in name only, and the tag becomes the escape hatch D3's visibility argument assumes it is not.
- **D5** — A `(regression)` check still requires concrete bare-label Evidence. Basis: the exemption is from red-green, not from evidence; a check with no evidence at all is the vacuity class 5.3.4 just closed.
- **D6** — The template says `.red`/`.green` are recorded *in addition to* the bare label. Basis: #21's second report; the gate has always required all three (`completionChecks` checks `label` and then `label.red`/`label.green`), and the current wording reads as replacement.

## Hidden Knowledge / Assumptions

- **A1** — Widening `SHARED_DURABLE_OWNER_FORMS` widens Review `Findings` and `## Expectation Coverage` too, not only `## Invalidates` which #20 reports. Basis: F1's three call sites and the comment declaring the sharing deliberate, so "a form added to one is never missing from the other". Accepted as correct rather than worked around: a form acceptable as an expectation's owner and unacceptable as a finding's owner would be the surprise.
- **A2** — Path existence is resolved against the repository root the gate already holds, so a path is judged where the gate runs. A consumer repo and this repo answer differently for the same string, which is intended: the claim being checked is "this repository keeps that file".

## Coupled Iteration Contract

Not required; no coupled artifacts.

## Risks / Trade-offs

- **An existence check makes a previously passing tasks.md fail if it named a path that never existed.** Accepted, and it is the point: that entry had no owner. No such entry can exist today, because a non-whitelisted path was already refused; only `keel/archive/…` paths could pass without existing, and those are this repository's own.
- **The `(regression)` tag can be misapplied to a behavioral check.** Mitigated by D4, by the tag being visible in the capsule, and by `keel-review-checklist` already requiring that a behavioral task's checks prove Acceptance. Not eliminated — a determined author can mislabel, as with any declaration.
- **Two issues in one change.** Accepted: they share one thesis, one file for most of the work, and one template surface. Splitting would duplicate the authoring and template tasks.

## Open Questions

None.
