## Why

Two failures in this repository share one shape: a check whose **form** is valid while its
**content** is empty or wrong. A `Durable owner:` may be a well-formed URL pointing at an issue with
nothing in it. A test's failure message may be a well-formed sentence naming a cause that is not the
cause. Both pass every deterministic gate, because both are correct in exactly the dimension a gate
can measure.

Neither can be fixed by making gates stricter. A gate that fetched a URL would trade the local,
offline, model-free properties that make its verdict worth trusting, and no gate can mechanically
judge whether a sentence misleads. `keel-expectation-slice-evidence-gates` already says the first
half of this out loud — "a gate runs without network and cannot confirm that a URL resolves" — and
then names nobody who does. This change names the semantic review layer.

The second instance is the argument for acting now. This repository fixed the misleading-diagnostic
class in 5.2.3, and in 5.7.0 the same class reappeared in a brand-new test. A fix that corrects
instances without leaving a recurrence guard is a fix with a half-life.

## What Changes

- `keel-review-checklist` gains two checks under its ownership and evidence sections:
  - a durable owner declared as a URL must already carry the content it claims to hold **at the
    moment it is cited**; create the content first, then reference it;
  - a failure message must name the actual cause, and one condition guarding two distinct failures
    must be split.
- The spec states that these are semantic-review responsibilities, closing the gap where the
  durable-owner requirement admits a gate cannot check content and leaves the check unassigned.
- Both checks stay out of the deterministic gates. This is stated as a requirement rather than left
  implicit, so a later change cannot quietly move them.

No behavior change to any gate, command, or config surface.

## Capabilities

### Modified Capabilities
- `keel-expectation-slice-evidence-gates`: the durable-owner requirement names semantic review as
  the layer that checks a reference's content, and a new requirement assigns the
  failure-message check to the same layer.

## Impact

- **Code**: `src/skills/keel-review-checklist/SKILL.md` and its `plugins/keel/skills/` copy,
  `scripts/validate_plugin.py`, `keel/CHANGELOG.md`.
- **Dependencies**: none.
- **Risk — the checks become gate checks later.** Mitigated by stating the layering as a
  requirement with its reason, so moving them requires editing a spec that explains why not to.
- **Risk — a checklist nobody reads.** Neither check is mechanically enforceable, so both depend on
  being read at the completion gate. Accepted: that is the layer's whole nature, and both entries
  are written as a concrete question rather than a principle.
- **Out of scope**: any network access from a gate; any attempt to judge whether reasoning or
  wording is *good* rather than whether it is present and accurate.
- **Authority**: https://github.com/TanglmChris/keel/issues/33 and its second-instance comment.
- This change was **admitted to an unattended run** by the `auto` label on issue #33, evaluated by
  `keel triage`. Admission started the work and decided nothing in it.
