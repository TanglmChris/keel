## Context

`keel gate task-complete` refuses a red-green task whose `M<n>.red` Evidence is
missing or a placeholder. It cannot read the failure that Evidence describes, so
a red that failed for the wrong reason satisfies it exactly as well as one that
failed for the right one. Issue #116 measured two such reds in a single session,
both found by a person looking at output that seemed off.

## Goals / Non-Goals

**Goals:**

- The reason a red is expected to fail is written down before the check is run.
- A recorded red carries a line of the failure it names, checkably.
- The obligation is heard while the author is deciding, not after the checks ran.

**Non-Goals:**

- Judging whether a red is honest. See D4.
- Requiring a signature on every check. See D3.
- Reading, running, or capturing process output. Gates stay local and model-free.

## Decisions

- F1 — `task-complete` requires concrete `M<n>.red` and `M<n>.green` Evidence
  under a red-green strategy and checks only that each is present and not a
  placeholder; nothing compares it to any expectation. Basis:
  `completionChecks` in `src/core/gates.js`, read 2026-09-08.
- F2 — A check's text is parsed from its `Verify` line by
  `/^(M[1-9]\d*)(?:\s*\(([^)\n]*)\))?:\s*(.*)$/`, and the whole text lands in the
  compiled capsule's `check`, so it is inside the contract fingerprint. Basis:
  `src/core/task-contract.js`, read 2026-09-08.
- F3 — 231 of 242 `.red` Evidence entries in this repository's archive already
  quote failure output in inline code — `` `openspec: not found` ``, a scenario's
  own refusal message, a diagnostic string. Basis: counted across
  `openspec/changes/archive/*/tasks.md`, 2026-09-08.
- F4 — Inline code already means "quoted material, not an assertion" in this
  repository, established by `withoutInlineCode()` (5.42.0) and extended to the
  disposition markers in 5.51.0. Basis: `src/core/task-contract.js`,
  `src/core/gates.js`.
- D1 — A check may end with `Fails with:` followed by an inline-code span; that
  span is the failure signature its red must show. Basis: F2 — writing it into
  the check text puts it inside the fingerprint for free, so a signature cannot
  be added, removed, or rewritten after the red was recorded without drift.
  Basis: F4 — the delimiter is the one this repository already uses for a
  literal, so where the string ends is unambiguous.
- D2 — When a check declares a signature, its `.red` Evidence must contain that
  literal string. Basis: F3 — authors already record the output; the check costs
  them nothing new and converts a habit into a criterion.
- D3 — A check with no `Fails with:` behaves exactly as today. Basis: making it
  mandatory would refuse every existing task and, worse, would be satisfied by
  any string an author chose after seeing the failure — which is the condition
  this change exists to remove, reintroduced as a formality.
- D4 — Keel does not judge whether the declared signature is a good one. Basis:
  an author can declare a string that any failure produces. What the declaration
  buys is that it was written **before** the run, where a retrofitted signature
  cannot be, and that it is in the fingerprint. This is the same contract
  `Discard reason:` and `--keep-evidence` already have: Keel records the claim
  and puts it where review can see it.
- D5 — `Fails with:` on a check that cannot have a red is refused at task-start
  by name: a `(regression)` check is exempt from red-green, and a strategy
  outside the red-green set records no `.red` at all. Basis: the alternative is
  a declaration silently doing nothing, which reads to its author as a check
  that is being enforced.
- D6 — A `Fails with:` marker with no inline-code span after it is refused rather
  than treated as absent. Basis: it is the shape of a typo, and the failure mode
  of ignoring it is the author believing a signature is enforced when none was
  parsed.
- D7 — The task-start red-green obligation warning names which owing checks
  declared a signature and which did not. Basis: 5.53.0 established that the
  obligation is stated at task-start rather than discovered at completion; the
  moment a signature is worth writing is the moment before the failing check is
  written, which is the same moment.

## Hidden Knowledge / Assumptions

- A1 — The value of a declared signature is entirely in its ordering relative to
  the run. A signature written after the failure was observed is a transcription;
  one written before it is a prediction, and only a prediction can be wrong.
  Keel cannot observe that ordering — it enforces the fingerprint, which makes a
  post-hoc edit visible rather than impossible. Durable owner:
  https://github.com/TanglmChris/keel/issues/116

## Risks / Trade-offs

- An author can satisfy D2 with a string that always appears (`Error`, or the
  scenario's own name). D4 accepts this: the declaration is reviewed, not
  verified, and a weak one is at least visible in the contract.
- The signature lives inside the check text, so an author refining the wording of
  a check after recording the anchor moves the fingerprint. That is the existing
  behavior of every check, and issue #115's `--keep-evidence` is the escape.

## Open Questions

None.
