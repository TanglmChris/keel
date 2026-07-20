<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Omitted fields inherit versioned defaults: Owner is the current Keel agent,
     Mode is implementation, Read is this change's proposal/design/specs/tasks
     plus discovered repository context, Acceptance derives from Covers, autonomy
     defaults to hard-stop, and commit/push/sync/archive stay unauthorized. -->

## 1. Record-compatible template anchor

- [ ] 1.1 Emit the template Contract anchor as `- Contract: pending` and update the needle
  - Covers:
    - keel-core-gates / The tasks template emits a record-compatible Contract anchor
  - Touch:
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: evidence-first
    - M1: a task scaffolded from the shipped template carries the literal `- Contract: pending` anchor, and `keel gate task-start --record` anchors it to a fingerprint line with no prior manual editing (no `record-refused`)
    - M2: both template copies emit `- Contract: pending` and no longer emit the descriptive suffix; the `validate_plugin.py` needle requires the bare form
    - M3: `npm test` passes with the updated template needle
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Expectation Coverage

- E1: record-compatible template anchor — both template copies emit `- Contract: pending`, the validator needle requires the bare form, and `task-start --record` anchors a fresh scaffold without manual editing. Covered by: 1.1
