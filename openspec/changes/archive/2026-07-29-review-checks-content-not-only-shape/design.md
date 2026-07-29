## Context

Issue #33 was filed after 5.4.0's expectation E5 cited issue #32 as a durable owner while that issue
had zero comments. The claim E5 made — that a rejected proposal's reasoning was "recorded where a
future reader will find it" — was false at the moment both gates returned `pass`. It was caught
because someone happened to run `gh issue view`, not because anything asked.

The second instance arrived in 5.7.0. A new triage scenario guarded two distinct failures with one
condition, so a wrong verdict was reported as an attempted network access. That is the class
`diagnostics-must-not-mislead` fixed in 5.2.3 — reappearing in a repository that had already fixed
it, in a test written by the agent that had just read the rule.

## Goals / Non-Goals

**Goals:**

- Assign the content check to the layer that can make it.
- State why it does not belong in a gate, so the reason survives the next person who wants to
  "strengthen" the gates.
- Write both entries as a question a reviewer can answer, not a principle they can agree with.

**Non-Goals:**

- Any network access from a gate.
- Judging whether reasoning is sound or wording is elegant. Both checks are about accuracy and
  presence, not quality.
- Re-opening the durable-owner *form* vocabulary, which 5.2.4 settled.

## Decisions

- **F1** — `openspec/specs/keel-expectation-slice-evidence-gates/spec.md:259` already states "A gate
  runs without network and cannot confirm that a URL resolves or that an archive path is the right
  one, so a whitelist of prefixes verifies nothing beyond spelling." It assigns the resulting check
  to nobody. Basis: read 2026-07-29.
- **F2** — 5.2.3 shipped `diagnostics-must-not-mislead`, which corrected specific misleading
  diagnostics and added no recurrence guard. The class reappeared in 5.7.0's `triage-declaration`
  scenario. Basis: `keel/CHANGELOG.md`; the 5.7.0 instance is recorded on issue #33.
- **F3** — `keel-review-checklist` already owns "Expectation and follow-up ownership" and the
  behavioral-evidence checks, so both new entries land beside checks of the same kind rather than
  creating a section. Basis: read 2026-07-29.

- **D1 — Both checks belong to semantic review, and the spec says so.** Basis: F1. The gap is not
  that Keel lacks a mechanism; it is that the requirement admits the gate cannot check content and
  then stops. Naming the owner is the whole fix.
- **D2 — Neither check may become a deterministic gate check, and the reason is recorded.** A gate
  that fetched a URL would be non-local, non-offline, and would fail differently on a plane than in
  CI; a gate that judged whether a message misleads would need a model. Basis: issue #33's own
  analysis and the properties `keel-core-gates` depends on. Recorded as a requirement so the next
  person to propose it reads why first.
- **D3 — The durable-owner check binds at citation time, not at archive time.** The wording is "must
  already carry the content when it is cited". Basis: the 5.4.0 case passed both gates and was
  caught late; a check that only runs at archive finds the same fact after the reauthorization it
  should have prevented, which is the reasoning `## Invalidates` already uses.
- **D4 — The failure-message check names the specific trigger: one condition guarding two distinct
  failures.** Basis: a general instruction to "write clear messages" is unactionable, and the
  5.7.0 instance had a precise structural cause — `if a is None or a["status"] != x` reporting the
  first failure's message for the second failure's case. Naming the structure makes it findable in
  review.
- **D5 — Entries are written as questions with a concrete failing example.** Basis: F3's neighbours
  are written the same way, and a reviewer scanning a checklist answers questions faster than they
  evaluate principles.

## Hidden Knowledge / Assumptions

- **A1** — Both checks are only as good as the review being performed. Nothing enforces them, and
  nothing can. Basis: D2. Owner: the completion gate's semantic Review, which is where the
  checklist is already invoked; this change adds no enforcement and must not imply it did.

## Risks / Trade-offs

- **A checklist entry nobody reads changes nothing.** Accepted and unmitigable by construction —
  the alternative is a gate, and D2 records why that is worse. The mitigation available is wording:
  both entries name a concrete failing case, which is easier to match against than a principle.
- **Two entries in a checklist that must stay short.** `token discipline` in the protocol pushes
  the other way. Accepted: two lines, and both replace a failure mode that has now occurred twice.

## Open Questions

None.
