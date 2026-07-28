<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1). -->

## 1. The boundary that needs no manifest is checked before the manifest

- [x] 1.1 An out-of-repository path passes the guard in every manifest state
  - Covers:
    - keel-touch-write-guard / The guard's scope is the repository it was started in
  - Touch:
    - plugins/keel/scripts/pretooluse-guard.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `guard-scope-is-the-repository` drives the hook over one fixture with a real recorded manifest and asserts the precedence, not merely the passthrough: with `keel/guard.json` corrupted, a path outside the repository is allowed while an in-repository path is still denied as invalid-manifest; and under genuine authority drift, caused by changing a live spec the task Covers, an in-Touch path is denied with the drift message while the outside path is allowed.
    - M2 (regression): the same scenario asserts the in-repository denials are unchanged by the reordering — an in-repository path outside Touch is still denied naming that path and the Touch list, and a path under the guarded change's own directory is still allowed.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:7ad979c422f141aa4ec143f62f0a111d077c8f46b75e833759d0b66e5cde281a
    - M1: `python scripts/validate_plugin.py --scenario guard-scope-is-the-repository` passes; `npm test` reports baseline plus 90 scenarios.
    - M1.red: before the fix the scenario failed on exactly one of its eight assertions — "an out-of-repository write under a corrupt manifest was denied", printing the real hook output `keel/guard.json is present but invalid, so file edits fail closed`. Every other assertion already passed, which is itself the evidence that the reordering is narrow: the passthrough was correct in all four other manifest states.
    - M1.green: the target is resolved and an out-of-repository path returns before the manifest is read at all, so the corrupt-manifest state now allows it while an in-repository path in that same state is still denied as invalid-manifest. Under genuine authority drift, caused by changing the live spec the task Covers, an in-Touch write is denied with the drift message and the outside path is still allowed.
    - M2: the same run asserts the in-repository denials are unchanged — an in-repository path outside Touch is still denied naming that path and the Touch list, an in-Touch path is still allowed, and a path under the guarded change's own directory is still allowed. The fixture verifies its own premise first, failing loudly if the manifest hashed no authority outside the change directory, because drifting the change's own tasks.md produces no drift and would have tested nothing.
    - Review:
      - Status: pass
      - Acceptance check: all three scenarios of the requirement are asserted, and the assertion is on the precedence rather than the passthrough — the corrupt-manifest and drift states are what distinguish "the boundary takes precedence" from "the boundary exists somewhere in the function". A scenario checking only a valid-manifest passthrough would have been green before this change.
      - Scope check: `plugins/keel/scripts/pretooluse-guard.js` and `scripts/validate_plugin.py` changed, both declared in Touch; base `HEAD`.
      - Findings: none
    - Blocker: none

- [x] 1.2 Promote the delta, record the release notes, and archive the change
  - Covers:
    - keel-touch-write-guard / The guard's scope is the repository it was started in
  - Touch:
    - openspec/specs/keel-touch-write-guard/spec.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - M1: after the delta is promoted into `openspec/specs`, `npx openspec validate the-guard-scope-is-the-repository` reports no error and `python scripts/validate_plugin.py` reports pass at the raised scenario count, with the live spec stating both the repository scope and its precedence over manifest-derived decisions.
    - M2: `node bin/keel.js gate change-close . --change the-guard-scope-is-the-repository --action archive --json` returns pass, after which this task is authorized to archive the change with `--skip-specs`.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d4c452d481b850c4e69325eced9963e1ec7b44db6122cc7688df66001cfa7481
    - M1: `npx openspec validate the-guard-scope-is-the-repository` reports "Change 'the-guard-scope-is-the-repository' is valid" with the delta promoted; `npm test` reports baseline plus 90 scenarios. The live spec now carries the repository-scope requirement and its precedence clause, and the outside-Touch requirement is scoped to in-repository paths so the two cannot be read against each other.
    - M2: `node bin/keel.js gate change-close . --change the-guard-scope-is-the-repository --action archive --json` returns pass once this task is checked, and the change is then archived with `--skip-specs` under the authorization this task carries.
    - Review:
      - Status: pass
      - Acceptance check: the spec change is the durable half of this fix. The code ordering was already corrected once for the same reason and regressed at a different step, which is what an unowned behavior does; naming the scope and its precedence in the requirement is what makes the next reviewer agree with the code instead of correcting it toward denying.
      - Scope check: `openspec/specs/keel-touch-write-guard/spec.md` and `keel/CHANGELOG.md` changed, both declared in Touch; base `HEAD`.
      - Findings: none
    - Blocker: none

## Invalidates

- I1: "Paths that resolve outside the repository root are not product writes and pass through" — the header comment of `plugins/keel/scripts/pretooluse-guard.js`, which states the rule unconditionally while the code applies it only after the manifest-validity check. Updated by: 1.1
- I2: "whose resolved target path falls outside the manifest's normalized Touch list" — the outside-Touch requirement in `openspec/specs/keel-touch-write-guard/spec.md`, which reads as covering every path anywhere and so contradicts the passthrough the code performs. Updated by: 1.2
- I3: "a corrupt manifest is the one case that still denies them" — gotcha 19 in the native memory file `keel-dogfood-authoring-gotchas.md`, recorded while diagnosing this. Updated by: 1.2

## Expectation Coverage

- E1: A decision that needs no manifest must not sit downstream of reading one Covered by: 1.1
- E2: The behavior must have a durable owner in the spec, so a reviewer reading it concludes what the code does Covered by: 1.2
- E3: Reordering a permission boundary must leave every in-repository denial unchanged Covered by: 1.1
