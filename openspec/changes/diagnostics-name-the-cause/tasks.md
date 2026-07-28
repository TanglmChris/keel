<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1). -->

## 1. Diagnostics name the thing the author has to change

- [x] 1.1 A Covers question reference is the subject of its entry, not any substring of it
  - Covers:
    - keel-task-capsule / A Covers question reference is the subject of its entry
    - keel-validation-runner / A narrowed refusal is asserted from both sides
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `covers-question-reference-scope` drives `node bin/keel.js gate task-start` over two fixtures and asserts both sides of the narrowed match: a `Covers` entry that opens with a fact reference and names a resolved `Q1` in its supporting text produces no `unresolved-authority` diagnostic, while an entry that opens with `Q1` and declares no authorized fallback still produces one naming `Q1`.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d015b122ec667a1e7ee717dd82079145c650af8f6995467ae620f94712b200b6
    - M1: `python scripts/validate_plugin.py --scenario covers-question-reference-scope` passes, and `npm test` reports baseline plus 82 scenarios with the neighbouring `unresolved-authority-names-field` scenario still passing.
    - M1.red: before the fix the scenario failed with "naming a resolved question as supporting detail still demands a fallback for it", printing the real diagnostic for the out-of-scope fixture: `Q1 is referenced in Covers but task 1.1 declares no authorized fallback.` The in-scope fixture was already refused, so the red isolated exactly the reported defect.
    - M1.green: after matching the identifier only where it opens a Covers entry, the fixture whose entry opens with `F13 (Q1 resolved: …)` produces no `unresolved-authority` diagnostic while the fixture whose entry opens with `Q1:` still produces one naming `Q1`.
    - Review:
      - Status: pass
      - Acceptance check: both scenarios of the requirement are asserted in one run — the subject fixture proves `task-start` still refuses and names the question, the detail fixture proves a cited resolved question is no longer treated as unresolved authority. The refusing case is what distinguishes the narrowing from a deletion of the check.
      - Scope check: only `src/core/task-contract.js` and `scripts/validate_plugin.py` changed, both declared in Touch; base `HEAD`. The change directory's own tasks.md carries Evidence under the record-write layer.
      - Findings: none
    - Blocker: none

- [ ] 1.2 A non-concrete check names the unfilled-slot token that made it non-concrete
  - Covers:
    - keel-task-capsule / A non-concrete check names the token that made it non-concrete
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `non-concrete-check-names-token` asserts that a `M2` check carrying a bare unfilled slot outside inline code yields a `missing-command-check` diagnostic whose message contains that slot text, that replacing exactly what the diagnostic names removes the diagnostic, and that a `M2` whose value is `pending` keeps the unqualified wording with no token named.
  - Evidence:
    - Contract: pending
    - M1: pending
    - M1.red: pending
    - M1.green: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

- [ ] 1.3 A task declaring no verification form reports one problem, and no defaulted field is required
  - Covers:
    - keel-task-capsule / Expanded v3 tasks normalize through the same compiler
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `absent-verification-form-is-one-problem` asserts that a task declaring neither `Verify` nor `Commands` produces a single diagnostic naming `Verify` as the compact field to add, and produces no `missing-field` diagnostic for `Owner`, `Mode`, `Read`, `Acceptance`, `Report`, `Candidate Boundary`, or `Stop Rules`.
    - M2: the same scenario asserts that an expanded task declaring `Commands`, `Covers`, `Evidence` and a boundary but omitting every defaulted field passes `node bin/keel.js gate task-start`, that the same task with `Commands` removed still fails, and that a `Candidate Boundary` diagnostic appears only once the task declares `Coupling: required`.
  - Evidence:
    - Contract: pending
    - M1: pending
    - M1.red: pending
    - M1.green: pending
    - M2: pending
    - M2.red: pending
    - M2.green: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

- [ ] 1.4 task-complete refuses to infer a task that has never started
  - Covers:
    - keel-core-gates / task-complete infers only a task that has started
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `task-complete-selection-requires-a-started-task` asserts that `node bin/keel.js gate task-complete` with no task named refuses on selection when the first unchecked task records no fingerprint in its Evidence `Contract` anchor, that the message names the inferred task, the most recently checked task, and the explicit selection flag, that the same change passes selection once that anchor records a fingerprint, and that `task-start` with no task named still selects the first unchecked task.
  - Evidence:
    - Contract: pending
    - M1: pending
    - M1.red: pending
    - M1.green: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 2. The shipped statements agree with the shipped behavior

- [ ] 2.1 Promote the deltas, restate the affected authoring rules, and archive the change
  - Covers:
    - keel-task-capsule / A Covers question reference is the subject of its entry
    - keel-core-gates / task-complete infers only a task that has started
  - Touch:
    - openspec/specs/keel-task-capsule/spec.md
    - openspec/specs/keel-core-gates/spec.md
    - openspec/specs/keel-validation-runner/spec.md
    - openspec/schemas/keel-spec-driven/schema.yaml
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/schema.yaml
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - AGENTS.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - M1: after the deltas are promoted into `openspec/specs`, `npx openspec validate diagnostics-name-the-cause` reports no error, `python scripts/validate_plugin.py` reports pass at the raised scenario count, and both copies of `schema.yaml` and both copies of the tasks template state that an unresolved question blocks only when it opens a Covers entry.
    - M2: `node bin/keel.js gate change-close . --change diagnostics-name-the-cause --action archive --json` returns pass, after which this task is authorized to archive the change with `--skip-specs`.
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Invalidates

- I1: "without an authorized fallback blocks implementation" — the `tasks` instruction prose in both copies of `openspec/schemas/keel-spec-driven/schema.yaml`. It stays true only for a question that opens a Covers entry. Updated by: 2.1
- I2: "requires an authorized fallback" — the Covers slot comment in both copies of `openspec/schemas/keel-spec-driven/templates/tasks.md`. Updated by: 2.1
- I3: "the parser falls back to expanded-v3 mode (demands Owner/Mode/Commands/…)" — gotcha 2 in the native memory file `keel-dogfood-authoring-gotchas.md`. After 1.3 an absent verification form is reported as one missing field, and the expanded set no longer names `Owner` or `Mode`. Updated by: 2.1
- I4: "Fill Evidence + Review → check the box → `keel gate task-complete`" — step 4 of the loop in the native memory file `dogfood-full-discipline.md`. That order is the reverse of the documented one and contradicts the loop recorded in `keel-dogfood-authoring-gotchas.md`; 1.4 makes the order load-bearing for no-arg selection. Updated by: 2.1
- I5: "must define a concrete public check" — the unqualified wording quoted in issue #28 item 5. After 1.2 it appears only for an empty or `pending` check. Durable owner: https://github.com/TanglmChris/keel/issues/28

## Expectation Coverage

- E1: A diagnostic must name the field, token, or task the author has to change, rather than a consequence of it Covered by: 1.1, 1.2, 1.3, 1.4
- E2: A narrowed refusal must keep a case that still refuses, so the narrowing cannot be mistaken for a removal Covered by: 1.1, 1.3
- E3: Every shipped statement about the changed rules must be corrected in the same change Covered by: 2.1
