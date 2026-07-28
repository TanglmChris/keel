<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1). -->

## 1. The record is read the way it is written

- [x] 1.1 A task body ends at the next task or the next heading
  - Covers:
    - keel-task-capsule / A task body ends at the next task or the next heading
  - Touch:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `task-body-ends-at-heading` asserts that a tasks file whose `## Invalidates` section quotes an unfilled-slot token inside double quotes passes `node bin/keel.js gate task-start` for its last task, that the same quoted phrase still satisfies the searchable-phrase check, that a task group heading is not appended to the preceding task's last field, and that the `--record` anchor search for the last task does not reach a `Contract` line placed in a trailing section.
    - M2 (regression): the compiled fingerprint of a task is byte-identical before and after the extent change for a fixture carrying both trailing sections, proving the parser fix moves no anchor in any live change.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:131192b2c7bd11daa7700f828cfa5babebf7163717a3b2570244a63129176e19
    - M1: `python scripts/validate_plugin.py --scenario task-body-ends-at-heading` passes; `npm test` reports baseline plus 88 scenarios.
    - M1.red: before the fix the scenario failed with `missing-field: Evidence must be concrete.` for the last task — issue #29 exactly, the gate blaming a task whose own Evidence is fine for a token quoted in a trailing section.
    - M1.green: the last task passes with the slot-carrying phrase double-quoted in `## Invalidates`, and the same run proves the phrase check is still satisfied, because the control fixture with an unquoted entry still produces `invalidation-phrase`. The group heading no longer appears in the preceding task's compiled fields, and `--record` leaves the stray `Contract` line planted inside the trailing section untouched.
    - M2: measured directly through a stash window over `src/core/task-contract.js` and `src/core/gates.js` on one fixture carrying a group heading and both trailing sections. Before the change: `1.1` = `2f723a87…a541d17`, `2.1` = `5e048136…ba7cbf05`. After: byte-identical for both. The two values are now pinned in the scenario, so a later extent or capsule-shape change cannot move an anchor silently; the failure message says why that matters.
    - Review:
      - Status: pass
      - Acceptance check: all four scenarios of the requirement are asserted — the trailing section, the group heading, the anchor search, and the phrase check that now coexists with the concreteness test. The last one is the point of the change: the two checks were never in conflict, so fixing the extent lets the same text satisfy both, and the control fixture proves the phrase check was not simply weakened.
      - Scope check: `src/core/task-contract.js`, `src/core/gates.js`, and `scripts/validate_plugin.py` changed, all declared in Touch; base `HEAD`.
      - Findings: none
    - Blocker: none

- [ ] 1.2 Completion requires a recorded start fingerprint
  - Covers:
    - keel-core-gates / Completion requires a recorded start fingerprint
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `completion-requires-a-recorded-anchor` asserts that `node bin/keel.js gate task-complete` with an explicitly named task whose `Contract` anchor reads `pending` does not pass and names both the anchor and `task-start --record`, that the same task passes once the anchor holds a compiled fingerprint, and that `task-start` reports no problem for the unrecorded task.
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

- [ ] 1.3 Promote the deltas, restate the recording step, and archive the change
  - Covers:
    - keel-core-gates / Completion requires a recorded start fingerprint
    - keel-task-capsule / A task body ends at the next task or the next heading
  - Touch:
    - openspec/specs/keel-task-capsule/spec.md
    - openspec/specs/keel-core-gates/spec.md
    - openspec/schemas/keel-spec-driven/schema.yaml
    - assets/openspec/schemas/keel-spec-driven/schema.yaml
    - AGENTS.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - M1: after the deltas are promoted into `openspec/specs`, `npx openspec validate the-gate-reads-what-it-promises` reports no error, `python scripts/validate_plugin.py` reports pass at the raised scenario count, and both copies of `schema.yaml` plus both protocol documents state that completion requires a recorded anchor. The bootstrap block stays within its byte budget.
    - M2: `node bin/keel.js gate change-close . --change the-gate-reads-what-it-promises --action archive --json` returns pass, after which this task is authorized to archive the change with `--skip-specs`.
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

- I1: "record the fingerprint in the task's Evidence `Contract` line before implementation" — the Completion gates paragraph in `AGENTS.md`, which describes recording as a step of the loop rather than as a precondition completion enforces. Updated by: 1.3
- I2: "pass `keel gate task-complete` before checking complete" — the one-line loop in `assets/bootstrap/AGENTS.md`, which names the gate but not the recording it now requires. Updated by: 1.3
- I3: "Quoting a token like an angle-bracket slot inside either section therefore makes the Evidence non-concrete" — the 5.3.6 entry in `keel/CHANGELOG.md`, and the same claim in the 5.3.7 entry. True when written, false after 1.1. Updated by: 1.3
- I4: "AND Expectation Coverage are absorbed into the LAST task's Evidence field" — gotcha 2b in the native memory file `keel-dogfood-authoring-gotchas.md`, including the hard-contradiction paragraph that follows it. Updated by: 1.3
- I5: "the fingerprint guarantee reads as unconditional but holds only for tasks that recorded an anchor" — the statement of the defect in issue #30 and in the 5.3.7 release notes. Durable owner: https://github.com/TanglmChris/keel/issues/30

## Expectation Coverage

- E1: A change-level section must never be read as a field of the task that happens to precede it Covered by: 1.1
- E2: A guarantee the protocol states unconditionally must either hold unconditionally or be refused Covered by: 1.2
- E3: The shipped protocol documents must state the recording step as the precondition it becomes Covered by: 1.3
