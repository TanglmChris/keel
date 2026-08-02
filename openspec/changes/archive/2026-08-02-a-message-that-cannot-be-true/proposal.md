# A message that cannot be true

## Why

Three places in Keel state something the reader cannot act on, and in each the
truth had no way to be written.

**The Review has no way to say a finding was fixed.** `keel-core-gates` says
"**WHEN** Review identifies an *unresolved* finding" and
`keel-review-checklist` says "each *unresolved* finding with a durable owner" —
both scope ownership to findings that are still open. `findingOwnerIsDurable` in
`src/core/gates.js:352` applies it to every non-`none` Findings value. A finding
found and fixed inside the same task has no accepted form, so `task-complete`
refuses it. In 5.11.0 task 1.4 this happened live: "Closed here; no follow-up is
owed" was refused, and the only way through the gate was to write
`Discard reason:` for something that had been repaired, not dismissed. The
archive now records a fix as a discard. `## Invalidates` already has the missing
slot — `Updated by:` naming tasks of this change is exactly "closed here" — and
Findings was never given the equivalent.

**A single failure message covers several distinct failures.** Issue #43 records
the shape caught by `keel-review-checklist` in three consecutive changes:
`if <the run did not work> or <the output lacks a specific thing>:` followed by
one `report(...)` describing only the second disjunct. When the first fires the
sentence is false, and it sends the reader to a place with no problem in it.
Measured across `scripts/validate_plugin.py`: 1069 report-then-return assertion
sites, 287 with an `or` test, and **68** where a run-or-verdict guard is OR'd
with a membership claim — the exact shape, in the file every other correctness
claim in this repository rests on. The three that were caught are the three
someone happened to look at.

**The write guard refuses with advice that cannot be followed.** When the
guarded change is archived, `taskIsChecked` cannot read its `tasks.md`, reads
that as "not checked", and falls through to the Touch comparison. The denial
names a task inside an archived change and says to "update the task authority
and reauthorize", which is not possible for that task. `keel guard status`
already classifies this state correctly as `drifted`; the hook enforcing the
manifest does not. Measured live at the start of this change: the first write
was refused against `the-name-is-not-the-thing#2.1`, archived one commit earlier.

## What Changes

- Review `Findings` gains a third disposition. Alongside a durable owner and a
  discard reason, a finding may be recorded as **resolved inside this task**,
  naming the evidence that proves it. The check moves from "every finding needs
  an owner" to what the spec and the checklist already say: every *unresolved*
  finding does.
- `keel-review-checklist` and `AGENTS.md` state all three dispositions and the
  criterion for choosing between them, so the choice is not decided by whichever
  marker the gate happens to accept.
- The validation suite gains a scenario counting the OR'd-guard assertion shape
  in `scripts/validate_plugin.py` against a recorded number. Adding one fails the
  suite and names the new site; removing one without lowering the number also
  fails. Issue #43 proposed a lint, which 68 pre-existing sites make unshippable
  as a pass/fail rule; a recorded count is enforceable today and turns an
  unfixable wall into a debt that can only move down.
- The write guard distinguishes a manifest whose change directory is gone from a
  task it merely cannot match, and refuses the first by naming `keel guard clear`
  — the action that actually resolves it. It still refuses; failing closed is
  what stops an archive from silently disabling the guard.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-core-gates`: Review `Findings` accepts a resolved-in-this-task
  disposition carrying its evidence; the accepted-forms diagnostic names it.
- `keel-validation-runner`: the suite asserts the count of OR'd-guard assertion
  sites in `scripts/validate_plugin.py` equals a recorded number.
- `keel-touch-write-guard`: a manifest whose change no longer exists is refused
  as stale, naming the action that clears it.

## Impact

- `src/core/gates.js` — the Findings disposition check and its diagnostic.
- `src/skills/keel-review-checklist/SKILL.md` and its plugin projection.
- `plugins/keel/scripts/pretooluse-guard.js` — the stale-manifest branch.
- `AGENTS.md` and the managed blocks projecting it.
- `scripts/validate_plugin.py` — one new scenario plus coverage for the two
  behavior changes; no existing assertion is rewritten by this change.
- Risk: the recorded count is a number that must stay true. It has the same
  failure mode as the scenario count and the same fix — the suite refuses a
  stale one in both directions, not only when it rises.
