# Tasks

## 1. The heading test

- [x] 1.1 `parseTasks()` and `sectionBody()` decide what a heading is through one shared column-zero test, so an indented `##` line ends neither a task nor a section
  - Covers:
    - keel-task-capsule / A task body ends at the next task or the next heading / An indented heading does not end a task
    - keel-task-capsule / A change-level section ends at the next heading or the next task / An indented heading does not end a section
    - D1
    - D2
    - D3
    - F1
    - F2
    - F3
    - F4
  - Read:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the `task-body-ends-at-heading` scenario runs the real `keel gate task-start` on a task whose `Acceptance` list carries an indented `    ## …` line followed by a `Stop Rules` entry, and requires the compiled capsule to carry that stop rule. Fails with: `dropped the fields declared after an indented`
    - M2 (regression): the `section-boundary` scenario plants an indented `  ## …` line in a tail-position `## Invalidates` and `## Expectation Coverage`, each followed by an unclosed entry, and requires `task-start` and `change-close` to refuse that entry by name. Detects: `the shared heading test tolerates leading whitespace` -> `because it follows an indented`
    - M3 (regression): `npm test` reports no failing scenario, and the fingerprints `task-body-ends-at-heading` pins are unchanged
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if any pinned fingerprint moves, because F3 says no existing task contains the line this changes.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:cdd1eae0ecb7111240aae564522444c6fdde91c94dc9bd2cccbad862c2b517bb
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario task-body-ends-at-heading` reports the scenario passing. The new cell runs the real `keel gate task-start` on a task whose `Acceptance` list carries `    ## an indented line is not a heading` followed by a `Stop Rules` entry, and the compiled capsule carries that rule.
    - M1.red: fail, for the declared reason. `task-body-ends-at-heading: task-start dropped the fields declared after an indented \`##\` line; the task ended at a line that is not a heading (status 'pass').` Carries the declared signature `dropped the fields declared after an indented`. The status in that red is the finding F4 predicted: task-start passed with the declared stop rule gone and `"stop": []` in the capsule, measured first on a probe fixture before the cell was written.
    - M1.green: pass. Same command after `isHeadingLine()` (column-zero `/^##\s/`) was added to `src/core/task-contract.js`, exported, and used by both `parseTasks()` and `sectionBody()` in `src/core/gates.js`.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario section-boundary` reports the scenario passing, with two new tail-position cells: `## Invalidates` with `  ## an indented line is not a heading` before an unclosed `I2` refuses `I2` at task-start, and `## Expectation Coverage` with the same line before an unclosed `E3` refuses `E3` at change-close. Green on 5.72.0 before any code change, as a regression check should be. Each cell was also shown to fail on its own against the abandoned branch's D5 pattern in `sectionBody()`, the second by disabling the first.
    - M2.detects: `isHeadingLine()` changed to `/^\s*##\s/` — the shared heading test tolerates leading whitespace — made `section-boundary` fail with `section-boundary accepted an invalidation that closes nothing because it follows an indented \`##\` line; the section ended at a line that is not a heading.` Carries the declared failure `because it follows an indented`. Restored afterwards.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 184 scenarios, 1 skipped: output-survives-the-pipe.` `task-body-ends-at-heading` passed inside that run, which compares the two pinned fingerprints, so neither moved. The Stop Rule did not trigger.
    - Review:
      - Status: pass
      - Acceptance check: both halves are asserted through the real gates rather than by calling the helper. The task half's red is the one worth keeping: task-start returned `pass` on a task whose declared stop rule had vanished, which is the silent case the owner's decision removes. One predicate now decides for both readers, so the divergence cannot come back by editing either reader alone; the mutation is aimed at that predicate, which is where a future tidy-up would land.
      - Scope check: `git status --short` shows `src/core/task-contract.js`, `src/core/gates.js`, and `scripts/validate_plugin.py` — this task's Touch — plus this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1
    - E2
    - I1
    - I2
    - I3
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-task-capsule/spec.md
    - .claude/commands/opsx/apply.md
    - .claude/commands/opsx/archive.md
    - .claude/commands/opsx/propose.md
    - .claude/commands/opsx/sync.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this task's whole effect is version markers, a changelog entry, and a promoted spec. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, with the 5.73.0 section written into the stub
    - M2: `keel/CHANGELOG.md` 5.73.0 states that the 5.26.0 decision to keep two heading patterns is reversed, why, and what it costs a live change downstream
    - M3: the delta is promoted, `node node_modules/.bin/openspec validate a-heading-is-not-indented --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2339d794e184bd9d899dc470db915aad1239d69f0d4e41321c9749ecf6cf5a0e
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes; every marker moved 5.72.0 to 5.73.0 via `node scripts/bump_version.js minor`, and the 5.73.0 section was written into the stub rather than above it. The Stop Rule held.
    - M2: pass. `keel/CHANGELOG.md` `## 5.73.0 - a heading is not indented` states that 5.26.0 kept two patterns and was right about the tolerant one, that the task side was quieter than it looked (the measured `"stop": []` on a passing task-start), that the owner chose the strict direction, and that a live downstream change with an indented `##` in a task body will stop for reauthorization.
    - M3: pass. Both MODIFIED requirements are promoted into `openspec/specs/keel-task-capsule/spec.md`, `node node_modules/.bin/openspec validate a-heading-is-not-indented --strict` reports the change valid, `openspec validate --specs --strict` reports 26 passed, and `npm test` reports `validation --all passed: baseline plus 184 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the 5.26.0 section is left as written and the reversal lives in the new entry, because a reader of 5.26.0 needs to find that it was superseded, not a history that says something it never said. The entry credits what 5.26.0 got right, so the reversal is not misread as the tolerant pattern coming back.
      - Scope check: `git status --short` shows the version markers, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, and the promoted spec — this task's Touch — plus the three files 1.1 declared complete and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "The heading half stays as it was: the two spellings are not interchangeable" — the comment above
  `sectionBody()` in `src/core/gates.js`. The two readers now share one test; what stays true is that the
  tolerant spelling is the wrong one.
  Updated by: 1.1
- I2: "A task body ends at the next task or the next `##` heading, whichever comes first." — the comment
  in `parseTasks()` in `src/core/task-contract.js`, which says nothing about indentation while the
  pattern beneath it tolerated it.
  Updated by: 1.1
- I3: "The heading half was deliberately left alone, and that is the owner's decision." — the 5.26.0
  section of `keel/CHANGELOG.md`. History, left as written; the 5.73.0 entry records the reversal.
  Updated by: 2.1

## Expectation Coverage

- E1: An indented `##` line ends neither a task nor a section, and both readers decide through one test
  (D1, D2). Covered by: 1.1
- E2: The section half cannot be tidied back to the tolerant pattern without a failing scenario (D3,
  F2). Covered by: 1.1
