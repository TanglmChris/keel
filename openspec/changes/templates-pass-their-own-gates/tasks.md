<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1). -->

## 1. Following the template passes the gate that reads it

- [x] 1.1 A requirement written from the spec template validates on first run
  - Covers:
    - keel-validation-runner / A shipped template is validated by the tool that consumes it
  - Touch:
    - openspec/schemas/keel-spec-driven/templates/spec.md
    - assets/openspec/schemas/keel-spec-driven/templates/spec.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `spec-template-validates` builds a change whose delta is the shipped spec template with its author-facing slots filled, runs `openspec validate` on it through `run_openspec`, and asserts no error; it reports a skip rather than passing when the OpenSpec CLI is absent, and it asserts both shipped copies of the template are byte-identical.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1330df1293aec3a5f38219f56905af7ce4114f8a324c6c2d380afdd447999bee
    - M1: `python scripts/validate_plugin.py --scenario spec-template-validates` passes with the OpenSpec CLI on PATH; `npm test` reports baseline plus 86 scenarios.
    - M1.red: before the fix the scenario failed with the reporter's own error, from the real validator: `ADDED "the recorded feed status" must contain SHALL or MUST`. A first attempt produced a different red — `ADDED "" is missing requirement text` — because the requirement *name* slot is a comment too and the filler was stripping comments rather than replacing them; the spec template's comments are slots, so they are replaced, which is what an author does with them.
    - M1.green: the requirement body now carries the literal line `The system SHALL` before its behavior slot, so a requirement copied from the template validates unchanged. The added instruction comment naming the rule cannot be what makes the check pass, because the filler replaces comments with plain text before validation runs.
    - Review:
      - Status: pass
      - Acceptance check: the assertion runs the filled template through `openspec validate`, which is the tool that refused the reporter, rather than matching the template's prose — a template mentioning the rule only in a comment would satisfy a prose check while still failing the author. The skip path is exercised by the CLI-absent branch, and both shipped copies are compared byte-for-byte.
      - Scope check: both copies of `templates/spec.md` and `scripts/validate_plugin.py` changed, all declared in Touch; base `HEAD`.
      - Findings: none
    - Blocker: none

- [ ] 1.2 The tasks template shows the red-green shape it describes
  - Covers:
    - keel-validation-runner / A shipped tasks template carries a worked example of every strategy shape it documents
  - Touch:
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `tasks-template-red-green-example` fills the shipped tasks template's slots mechanically, runs `node bin/keel.js gate task-start` over every task the template defines, and asserts each passes; it asserts the red-green group carries a bare, a `.red`, and a `.green` Evidence entry for its untagged check and only a bare entry for its `regression`-tagged check, and that both shipped copies are byte-identical.
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

- [ ] 1.3 Promote the delta, record the release notes, and archive the change
  - Covers:
    - keel-validation-runner / A shipped template is validated by the tool that consumes it
  - Touch:
    - openspec/specs/keel-validation-runner/spec.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - M1: after the delta is promoted into `openspec/specs`, `npx openspec validate templates-pass-their-own-gates` reports no error and `python scripts/validate_plugin.py` reports pass at the raised scenario count.
    - M2: `node bin/keel.js gate change-close . --change templates-pass-their-own-gates --action archive --json` returns pass, after which this task is authorized to archive the change with `--skip-specs`.
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

- I1: "The current template only shows the flat form." — issue #28 item 2's closing suggestion, and the same claim in item 3 that "there is no worked example anywhere showing how red-green is supposed to look". Both stop being true at 1.2. Durable owner: https://github.com/TanglmChris/keel/issues/28
- I2: "requirement text" — the body slot of both copies of `openspec/schemas/keel-spec-driven/templates/spec.md`, which carries no modal verb and so cannot validate as copied. Updated by: 1.1
- I3: "16 traps" — the hook for `keel-dogfood-authoring-gotchas.md` in the native memory index, whose count changes as the template gaps close. Updated by: 1.3

## Expectation Coverage

- E1: An author who follows a shipped template exactly must not be refused by the gate that reads it Covered by: 1.1, 1.2
- E2: A template claim must be asserted by running the template, since prose beside a wrong example loses to the example Covered by: 1.1, 1.2
- E3: The two shipped copies of each template must stay identical Covered by: 1.1, 1.2
