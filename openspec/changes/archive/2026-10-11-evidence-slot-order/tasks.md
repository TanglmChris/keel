# Tasks

## 1. Slots in template order

- [x] 1.1 `--record` places each missing slot after its nearest present predecessor in template order
  - Covers:
    - keel-core-gates / Gate results expose capsule and fingerprint evidence / Record places added slots in template order
    - keel-core-gates / Gate results expose capsule and fingerprint evidence / Record fills a task's missing record slots
    - keel-core-gates / Gate results expose capsule and fingerprint evidence / Record keeps what the author already wrote
    - D1
    - D2
    - F1
    - F2
    - F3
  - Read:
    - src/core/gates.js
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario record-derives-skeleton` runs `--record` over an Evidence block holding `Contract: pending`, `Blocker: none`, `Reauthorizations: none` and requires the block's lines to equal the Contract line, `M1`, `M1.red`, `M1.green`, `M2`, `M3`, `M3.red`, `M3.green`, `M3.detects`, the Review block, `Blocker: none`, `Reauthorizations: none` in that order; and over a block holding a concrete `M1` line then `Review` it requires `M1.red` and `M1.green` directly after that `M1` line. Fails with: `record-derives-skeleton:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6e672219dea1d3cab7cc76609c3e186a23d7f4e3e44c3db53a3339f0335a8d25
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario record-derives-skeleton` reports `record-derives-skeleton scenario passed.`
    - M1.red: fail. Before the change the scenario reported `record-derives-skeleton: --record over Contract, Blocker and Reauthorizations left the block out of template order: [… 'Blocker: none', 'Reauthorizations: none', 'M1: pending', …]`, carrying the declared signature `record-derives-skeleton:`. This task's own `--record` showed the same shape: its `M1` slots landed after `Reauthorizations: none`, as they still sit here.
    - M1.green: pass. With `withEvidenceSlots` placing each missing slot after the last slot already placed, the scenario passes, and `core-gates`, `completion-requires-a-recorded-anchor`, and `touch-guard-record-layer` still pass.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `task-start --record` over both partial shapes and compares the Evidence block line by line with the expected order.
      - Scope check: `git status --short` lists `src/core/gates.js`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: Evidence blocks already written in the older Blocker-first order are not reordered; present slots never move (D2), and those blocks complete as they are.

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E2
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-core-gates/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js patch` moves every marker to the next patch version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-core-gates/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:43238ce81fa41c26af2a275be836c7b657b5ae00dbf9bf94bd853cdd51db1b44
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. After merging `main` (5.99.3, #264), `node scripts/bump_version.js patch` moved every marker to 5.99.4. With the 5.99.4 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its published copy, keeping its scenarios and adding one; `published-specs-validate-strictly` reports `31 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published requirement says where added slots go with its scenario, and the changelog names the issue and the order.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after merging `main` and the bump to 5.99.4 reports `validation --all passed: baseline plus 239 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: A partly written Evidence block comes out of `--record` in template order, so a later rewrite in that order matches its pending lines (D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
