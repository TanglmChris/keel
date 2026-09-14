## Context

Three closure forms, one unchecked. The check is a set difference between two identifier
lists that are already parsed and already in the same file — `Covered by:`'s cited
identifiers on one side, the named task's `Covers:` on the other. What makes it worth a
gate is not difficulty; it is that no reader performs it.

Alignment ran the quick path for the comparison itself, and the deep path for one
question the report left open: whether to adopt its second suggestion. That was settled
against measurement rather than by asking, because the repository answered it — see D3.

## Goals / Non-Goals

**Goals:**

- An entry that names identifiers and names a task is held to the claim it just made.
- A refusal says where the identifier actually is, so the fix is one edit rather than an
  investigation.
- The gate says how much of the section it compared, so a pass is not read as a warrant
  it does not carry.

**Non-Goals:**

- Requiring identifiers. See D4.
- Judging whether an expectation is *well* covered by the task that names it. The
  comparison is between two lists; whether the task's checks actually prove the
  expectation is `keel-review-checklist`'s, and stays there.
- Adopting the report's set-intersection rule. See D3.

## Decisions

- F1 — `Covered by:` is 117 of 146 E entries (80%) in the reporting repository, and the
  only closure form with no check: `Durable owner:` gained existence checking in 5.51.0,
  `Discard reason:` requires a reason. The existing code checks only that the named task
  exists and is checked (`src/core/gates.js`, `expectationProblems`). Basis: issue #133,
  and the function read 2026-09-14.
- F2 — Six of the 42 citing entries are wrong, in three shapes: three name a task of the
  change other than the one whose `Covers:` holds the identifier, two are the same
  identifier claimed as covered and deferred at once, one names an identifier no task
  covers. All six are archived and passed `change-close`. Basis: issue #133's table.
- F3 — Run over this repository's own 83 archived changes, the comparison fires **zero**
  times: 347 of 351 `Covered by:` entries cite no identifier at all, and the four that do
  are from the change archived hours before this one. Basis: a script over
  `openspec/changes/archive`, 2026-09-14. This repository's own convention is prose, so
  the rule is a no-op on its history and its evidence base is the reporting repository.
  Recorded because it is the honest answer to "did you test it on your own data": the
  archive cannot confirm this rule, and the scenario carries the whole proof.
- D1 — Compare at `change-close`, where `expectationProblems` already runs, and nowhere
  else. Basis: `## Invalidates` moved earlier than the close because declaring it early is
  what lets affected paths enter Touch before implementation. Coverage has no such
  consequence — nothing about a task's write boundary depends on it — so the close is
  where the whole-change assertion belongs and the earlier gate stays cheap.
- D2 — The refusal names where the identifier actually is covered, or that no task of the
  change covers it. Basis: the information is free — the same parse already has every
  task's `Covers:` — and the three shapes in F2 are told apart by exactly this. Without
  it the author is told a claim is wrong and must re-derive which of the three it is.
- D3 — Do **not** adopt the report's second suggestion, that one identifier may not appear
  on both a `Covered by:` entry and a `Durable owner:`/`Discard reason:` entry. Basis:
  measured. Over 83 archived changes it fires once, and that once is a false positive —
  an entry citing `D2` to state that D2 *is* covered by a task, so that the residue it
  owned could not be mistaken for D2. The rule cannot tell a claim from a contrast,
  because both are a mention. The report's own contradiction case (F2, two entries) is
  already refused by D1's comparison, which does not need to know why an identifier was
  mentioned — it only asks whether the task named actually names it back. A rule that
  reaches the same finding without the false positive is the one to ship.
- D4 — An entry citing no identifier is neither refused nor nudged. Basis: 58% of the
  reporting repository's entries and 99% of this one's are prose, and some expectations
  genuinely are ("documentation and skills follow the behavior changes above"). Forcing an
  identifier onto them manufactures a reference to satisfy a parser, which is the failure
  mode #116's closing note refused when it declined to require a line of output under
  every `.red`.
- D5 — Report the compared and uncompared counts on every close that has a section to
  report on, rather than only when something was skipped. Basis: the number that changes a
  reader's belief is the ratio, and a line that appears only sometimes teaches the reader
  that its absence means full coverage — which is the opposite of true in the repository
  where 99% is uncompared.
- D6 — `I<n>` is not compared. Basis: an `## Invalidates` entry has its own closure check,
  which already requires `Updated by:` to name tasks this change defines. An E entry citing
  an `I<n>` is a second and weaker claim about something already owned, and adding it would
  extend the rule past what F2 measured.

## Hidden Knowledge / Assumptions

- A1 — An identifier cited inside an E entry is a claim about that entry's subject rather
  than an incidental mention. Basis: measured at 534 real entries across two repositories
  — the rule fires 6 times and all 6 are defects, so the false-positive rate is 0 on the
  data that exists. It is not 0 by construction: an entry could mention an identifier for
  contrast, which is exactly what made D3's rule unsound. The difference is that this rule
  asks a question with a right answer (does the named task name it back) and D3's asks one
  with two innocent answers.

## Risks / Trade-offs

- A prose mention of an identifier inside an entry that also carries `Covered by:` is
  refused. The escape is to add the identifier to the task's `Covers:` — which is correct
  when it is a claim — or to reword, which is the shape the archive cannot measure
  (#70: a false stop leaves its trace in the author, not the archive). A1 records why the
  exposure is accepted; D2's message is what keeps the cost at one edit.
- One more thing `change-close` prints. D5 argues the ratio earns its line; if it turns out
  to fire on every change with nothing to act on, that is #135's subject and not a reason
  to make the line conditional and therefore misleading.

## Open Questions

None.
