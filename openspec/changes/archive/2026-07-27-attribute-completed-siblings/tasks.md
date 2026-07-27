<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. A finished task's work is not the next task's scope failure

- [x] 1.1 Withhold attribution for a path a completed sibling declares, and report the exclusion
  - Covers:
    - D1 a completed sibling's declared Touch withholds attribution from the selected task, derived from tasks.md with no new state
    - D2 the exclusion is reported rather than silent, because a base comparison cannot establish which task wrote a path
    - D3 only a checked sibling counts, because an unchecked task's Touch is a plan rather than a record
    - keel-core-gates / Dirty-worktree attribution is conservative / A completed task's uncommitted work is not the next task's scope failure
    - keel-core-gates / Dirty-worktree attribution is conservative / An unfinished task's Touch grants nothing
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: through the gate CLI in a real git repository, completing a task with an explicit base while a sibling task that is checked complete has uncommitted changes to a file in its own Touch returns pass instead of the outside-touch failure it returns today, and the result carries a warning naming both that path and the completed task that declares it. With the same sibling left unchecked the path still fails as outside-touch; a path no task declares still fails; a sibling whose Touch is none contributes no claim; and paths inside the selected task's own Touch stay unaffected. A new validator scenario locks every case and the full suite stays green
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e04ce872bdc1ec42fe9a104e74262715f50fcdba5bfe1cd2a337360fe8d37ea0
    - M1: a `completedSiblingOwners` helper collects, from the task list the gate has already parsed, every *checked* task of the change other than the selected one together with its declared Touch. `scopeEvidence` takes that list as a new optional parameter and, for each path that survives the existing filters, looks for an owner whose Touch covers it: when one is found the path is dropped from `problems` and a warning names both the path and the owning task; otherwise it becomes an `outside-touch` failure exactly as before. The sibling's Touch is read through the existing `touchEntries` without compiling its capsule, which also means `Touch: none` yields no claims because `isConcrete` rejects `none`. No new state, no manifest or capsule field, and the no-base branch is untouched
    - M1.red: the new `completed-sibling-attribution` scenario exited 1 with "a completed sibling's declared file was still attributed to the selected task: ['Changed path is outside Touch: src/shared.js', 'Changed path is outside Touch: src/stray.js']" — issue #13 item 2 reproduced in a real git repository, with the true failure (`stray.js`) and the false one (`shared.js`) side by side
    - M1.green: the scenario exits 0 across five checks, each against a fresh git repository with a real commit and real uncommitted work. A checked sibling's declared file is no longer attributed to the selected task; the undeclared `src/stray.js` still fails, so the check did not simply get weaker; the result carries a warning naming `src/shared.js` and task `1.1`; leaving that sibling unchecked restores the `outside-touch` failure, proving the checkbox is what grants the exclusion; and a sibling declaring `Touch: none` contributes no claim, so the path fails again. `npm test` reported "validation --all passed: baseline plus 73 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — the false failure from issue #13 is gone while the true one beside it survives, the exclusion is visible rather than silent, and both narrowing conditions (unchecked sibling, `Touch: none`) are asserted rather than assumed, satisfying D1, D2, D3 and both referenced scenarios
      - Scope check: pass — `src/core/gates.js` and `scripts/validate_plugin.py`, both within Touch, verified against `--base HEAD`
      - Findings: this change makes the gate that reported the problem also the gate that verifies the fix, so the scenario deliberately builds a real repository with a real commit rather than asserting on `scopeEvidence` in isolation — the defect was in what `git diff` returns versus what the task list says, and a unit-level fixture could not have shown it. One property is worth stating plainly because it is a limit rather than a bug: where two tasks could own a path the gate now resolves in the selected task's favour, so a genuine overlap is reported as a warning rather than a failure. The write guard is the control that can actually attribute authorship, at the moment of the write. Recorded in design.md risk A1. Discard reason: stated limit accepted with its mitigation, nothing remains to own
    - Blocker: none

## Expectation Coverage

- E1: a task is never failed for a path a finished task of the same change was authorized to write Covered by: 1.1
- E2: the per-task commit convention stops being an implicit requirement whose violation names the wrong file Covered by: 1.1
- E3: ambiguous attribution is reported, never silently resolved Covered by: 1.1
- E4: an unchecked sibling, an undeclared path, and a `Touch: none` sibling all still fail or grant nothing Covered by: 1.1
