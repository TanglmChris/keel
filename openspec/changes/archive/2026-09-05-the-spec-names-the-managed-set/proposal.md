## Why

`keel-openspec-surface-overlay`'s Purpose and its opening requirement still describe the managed overlay as covering "apply/archive". The code has managed four actions for some time — `OPENSPEC_OVERLAY_ACTIONS = ["propose", "apply", "archive", "sync"]` in `bin/keel.js` — and `propose` and `sync` arrived as *new* requirements appended to the same file rather than as edits to the statement that says what the set is. So the file says two things: the summary at the top says two actions, and the requirements below it cover four.

Measured across `openspec/specs/` (2026-09-05, 5.43.0): 9 statements in that one file name a proper subset of the managed set — 6 say `apply/archive` (Purpose, the opening requirement's name and body, and its three per-target scenarios) and 3 say `apply/archive/sync` about install and refresh, which cover `propose` too. Issue #86 reports the first of the nine.

Three other spellings look like the same drift and are not: `apply/archive/sync` in `keel-target-surface-diagnostics` is the doctor label, which excludes `propose` on purpose because that line counts state-changing command surfaces; `sync/archive decisions` in the archive requirement names what the agent owns, not what Keel overlays; and `authoring/apply/archive/sync` names all four with `propose` spelled as authoring. A check that read the file for action words would refuse all three, which is the failure this repository keeps repairing.

Issue #86 also asks why the Purpose line survived #79, which fixed nine similar drifts. The answer is structural: OpenSpec's delta format has operations for Requirements only — `ADDED`, `MODIFIED`, `REMOVED`, `RENAMED` — confirmed against openspec 1.6.0's own change parser. A spec's Purpose is written once when the spec is created and is edited directly thereafter; OpenSpec's generated placeholder says so in as many words ("Update Purpose after archive"). Nothing was going to route that line through a change, so nothing noticed it.

## What Changes

- The Purpose, the opening requirement's name and body, its three per-target scenarios, and the two install/refresh scenarios name the managed set the code maintains, so the top of the file agrees with the requirements below it.
- A new deterministic check asserts that agreement: the Purpose line and the requirement that states the managed overlay must each name every action in `OPENSPEC_OVERLAY_ACTIONS`, read from `bin/keel.js`. This is the same shape as the existing "Every overlay summary names the managed action set" requirement, which made the *runtime* summary derived and drift-checked; the spec's own statement of the set was left out of it.
- The check is two named locations, not a scan of the file. The three correct-looking spellings above stay untouched, and a check that could not tell them apart would be worse than the drift.

## Capabilities

### Modified Capabilities
- `keel-openspec-surface-overlay`: the "Keel overlays apply and archive surfaces" requirement is renamed and reworded to state the managed set rather than two members of it, and its scenarios cover the same set per target. The "Every overlay summary names the managed action set" requirement gains the spec's own statement of the set as a second place the derivation is checked, and states that a capability's Purpose is maintained by direct edit because no delta operation reaches it.

## Impact

- Affected files: `openspec/specs/keel-openspec-surface-overlay/spec.md` (the drifted statements), `scripts/validate_plugin.py` (the new check).
- No production code changes. `bin/keel.js` is read, not written: the managed set is already derived there, and this change makes the prose agree with it rather than moving the authority.
- Direction is a documentation correction plus a new failing-on-drift check. Nothing about installed behavior changes.
- The Purpose edit is a direct edit to the published spec because OpenSpec offers no delta operation for it; the delta in this change carries the requirement-level half.
