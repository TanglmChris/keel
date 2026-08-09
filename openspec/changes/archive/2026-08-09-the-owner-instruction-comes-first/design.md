## Context

`src/core/gates.js`'s `taskComplete` review checks (`reviewProblems`, around line 841-878)
produce a `finding-owner` problem when a task's Review `Findings` value is not `none` and names
no recognized disposition (`Resolved here:` evidence, `Durable owner:`, or `Discard reason:`/
`Discard rationale:`). The message it builds (lines 863-877) is, today:

```
Review Findings must be `none` or carry a disposition. A finding fixed in this task is
`Resolved here:` naming an `M<n>` check this task declares or a repo-relative path that exists;
one someone must still do is `Durable owner:` naming an absolute `https://…` tracker reference,
or any repo-relative path that exists — `keel/archive/…`, an `openspec/changes/…` artifact, or
the repository's own ledger; `keel/HANDOFF.md` is a pointer override rather than an owner; one
deliberately not being done is a `Discard reason:`/`Discard rationale:` prefix. Name a path
after `Durable owner:` so it reads as the owner rather than a file the finding mentions.
```

`openspec/specs/keel-core-gates/spec.md`'s "A finding resolved in its own task is recorded as
resolved" Requirement already has a scenario asserting the closing sentence's *content* ("The
accepted-forms diagnostic names all three dispositions" — "AND THEN it still directs a path to
be named after `Durable owner:` so it reads as the owner rather than a file the finding
mentions"). It does not assert the sentence's *position*, so today's trailing placement already
satisfies it.

## Goals / Non-Goals

**Goals:**

- Move the one actionable sentence to lead the message, right after its opening sentence, so a
  reader who has genuinely forgotten to name a path reads the instruction before the menu.
- Add a spec scenario that pins the order, not just the content, so a future edit cannot drift
  the sentence back to the end unnoticed the way it sat unnoticed for three prior measurements.
- Extend the existing `core-gates` validation scenario with order assertions on the same
  `finding_owner_message` capture it already builds.

**Non-Goals:**

- Changing any word in `DURABLE_OWNER_FORMS`, the three disposition markers, or any other
  diagnostic message. F1 below confirms this is the only message this change touches.
- Section 1 of `#49` (bare `D<n>` Covers references reported `Missing`) — a separate, unresolved
  material decision escalated twice already (2026-08-02, 2026-08-04). Touching it here would
  remix an owner-blocked decision into a diff whose whole point is being small and reviewable.
- The two still-open block-parsing addenda on `#49` (`Verify`'s `M<n>` continuation lines read
  as new entries) — flagged by the prior run as needing its own change, and it touches
  `fieldValues()`, which `Touch` compilation also reads. Out of scope here.
- Any change to what `task-complete` accepts, refuses, or exits with. `findingOwnerIsDurable()`
  and every problem code are untouched.

## Decisions

- D1 — Move the sentence by literal position only: same words, same clause boundaries, joined to
  the opening sentence with an em dash rather than left as a fourth, separate sentence. Basis:
  the goal is order, not rewording; keeping every other word verbatim keeps the diff a pure
  reorder that a reviewer can confirm by reading the two versions side by side.

- D2 — Verify by extending the existing `core-gates` scenario's `finding_owner_message` capture
  (`scripts/validate_plugin.py:11177`) with three single-cause `if` checks (instruction present,
  `Resolved here:` present, instruction's index precedes it) rather than one compound condition.
  Basis: `assertion-shape-count` (`#43`) already exists specifically to catch one `if` covering
  several distinct failures behind one message — the `help-lists-the-command-it-has` change hit
  this exact trap and split for the same reason. None of the three new checks use an `or`
  combining a membership test with a non-membership test, so `OR_GUARDED_ASSERTION_SITES` (75)
  is unaffected — confirmed at F2.

- D3 — Spec delta is `MODIFIED Requirements` on the existing "A finding resolved in its own task
  is recorded as resolved" Requirement, adding one sentence to its prose and one new Scenario,
  with the three existing Scenarios reproduced verbatim. Basis: this is the Requirement that
  already owns the `finding-owner` diagnostic's shape; the order constraint is a refinement of
  it, not a new capability concern.

- F1 — Verified 2026-08-09 by grep (`grep -rln "so it reads as the owner rather than a file"`,
  excluding `node_modules` and `openspec/changes/archive`): the sentence appears in exactly three
  places outside history — `src/core/gates.js` (the message itself), `openspec/specs/keel-core-
  gates/spec.md` (the scenario asserting its content), and `keel/CHANGELOG.md:67` (a 2026-08-04
  entry narrating the cross-line-Findings fix, which describes this same sentence "closes with"
  — see F3).

- F2 — Verified 2026-08-09 against the live tree (`node -e` probing `or_guarded_assertion_sites`-
  equivalent logic by reading `scripts/validate_plugin.py:21124` and the three new checks' AST
  shape by hand): none of the three new `if` statements is a `BoolOp`/`Or` test, so
  `or_guarded_assertion_sites()` does not walk into them; the recorded constant needs no change.

- F3 — `keel/CHANGELOG.md:67`'s 2026-08-04 entry reads "It closes with 'Name a path after
  `Durable owner:` so it reads as the owner rather than a file the finding mentions'" — true of
  the message *as it stood in the 5.28.0 release this entry documents*. After this change the
  sentence no longer closes the (current) message. This is a dated, historical CHANGELOG entry
  describing what was true at 5.28.0, not evergreen documentation of the current message shape;
  `## Invalidates` below records this with a discard rationale rather than editing history.

## Hidden Knowledge / Assumptions

- A1 — `reviewProblems()` builds `reviewFields.Findings` by reading the whole Review `Findings`
  entry (5.28.0's sibling-bound read), so the message text itself is unaffected by that mechanism
  — this change only touches the diagnostic string built when the entry has no recognized
  disposition, not how much of the entry is read.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- None beyond the output text of the `finding-owner` diagnostic changing, which is the point of
  the change. Any external tooling that greps this exact message for a specific substring
  position (none is known inside this repository — F1 found only the three files above, none of
  which parses the CLI's live output) would need to re-anchor; F1's grep is the evidence no such
  in-repo consumer exists.

## Open Questions

None.
