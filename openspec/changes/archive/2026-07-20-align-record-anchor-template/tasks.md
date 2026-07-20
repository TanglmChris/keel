<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Omitted fields inherit versioned defaults: Owner is the current Keel agent,
     Mode is implementation, Read is this change's proposal/design/specs/tasks
     plus discovered repository context, Acceptance derives from Covers, autonomy
     defaults to hard-stop, and commit/push/sync/archive stay unauthorized. -->

## 1. Record-compatible template anchor

- [x] 1.1 Emit the template Contract anchor as `- Contract: pending` and update the needle
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
    - Contract: keel-task-capsule/v1 sha256:01b9e740fe666cef9fdc7766bb06935244d7620d95df9331b2c4be1c1095b903
    - M1: both template copies now emit `- Contract: pending` (2 each) with 0 long-form anchors remaining; `keel gate task-start --record` anchored this task's own bare `- Contract: pending` to `sha256:01b9e740...` with no `record-refused` and no manual editing — dogfooding that a template-shaped anchor is record-able.
    - M2: both template copies emit `- Contract: pending` and no longer emit the `task-start capsule and fingerprint` suffix; the `validate_plugin.py` template needles (baseline `validate_openspec_schema` and the `compact-task-authoring` scenario) now require `- Contract: pending`.
    - M3: `npm test` reported "validation --all passed: baseline plus 51 scenarios" after both needles were updated to the bare anchor.
    - Review:
      - Status: pass
      - Acceptance check: pass — the shipped template emits the literal `- Contract: pending` anchor that `--record` accepts, and validation enforces the record-compatible form.
      - Scope check: pass — changes limited to Touch (both `keel-spec-driven` tasks template copies, `scripts/validate_plugin.py`) plus this change's own `tasks.md`.
      - Findings: none
    - Blocker: none

## Expectation Coverage

- E1: record-compatible template anchor — both template copies emit `- Contract: pending`, the validator needle requires the bare form, and `task-start --record` anchors a fresh scaffold without manual editing. Covered by: 1.1
