# Tasks

## 1. Strategy guidance

- [x] 1.1 Give the test-first skill a strategy-selection guide and name every evidence clause in it
  - Covers:
    - keel-verification-layering / Keel documents how to choose a Verify strategy / Every accepted strategy has a selection row
    - keel-verification-layering / Keel documents how to choose a Verify strategy / Every enforced evidence clause is named in the skill
    - D1
    - D2
  - Read:
    - src/skills/keel-tdd-or-test-first/SKILL.md
    - src/skills/keel-run-single-task-goal/guidance.md
    - openspec/changes/tdd-strategy-guidance/design.md
  - Touch:
    - src/skills/keel-tdd-or-test-first/SKILL.md
    - src/skills/keel-tdd-or-test-first/guidance.md
    - plugins/keel/skills/keel-tdd-or-test-first/SKILL.md
    - plugins/keel/skills/keel-tdd-or-test-first/guidance.md
    - scripts/validate_plugin.py
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario tdd-strategy-guide`: the canonical `guidance.md` beside `keel-tdd-or-test-first/SKILL.md` has a table row naming each strategy in `SUPPORTED_VERIFICATION_STRATEGIES` read from `src/core/task-contract.js`; the body names `Fails with:`, `Detects:`, `Measured:`, `(regression)`, `deferred to C`, and `artifact`; the body states that the strategy is chosen by what would make the Acceptance false; and both plugin copies are byte-identical to the canonical files. Fails with: `tdd-strategy-guide:` Detects: `the equivalence row deleted from the guidance table` -> `no selection row for equivalence`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario guidance-is-referenced-and-carries-no-criterion` passes with two guidance files, so the new one is referenced with its `executor_tier` condition and carries no criterion word.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario native-plugin-manifests` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bf83071183c065f5d448032e1fc131230057596a6647e8871a12765b8525824a (keel 5.170.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario tdd-strategy-guide` reports `tdd-strategy-guide scenario passed.` (exit 0): all seven strategies read from `SUPPORTED_VERIFICATION_STRATEGIES` have a row in the guidance table, the body names the six clauses and the selection criterion, and both plugin copies are byte-identical.
    - M1.red: fail. Before the guidance existed: `tdd-strategy-guide: keel-tdd-or-test-first has no guidance.md beside its SKILL.md.` (exit 1).
    - M1.green: pass. With `src/skills/keel-tdd-or-test-first/guidance.md` written (selection table, right and wrong choices, when a red adds information, which evidence form pays, a FIFO example), the body gaining the selection criterion, the `guidance.md` pointer with its `executor_tier: high` condition, the `Detects:`, `Measured:` and `(regression)`/`deferred to C<n>` paragraphs, and both files copied to the plugin, the scenario passed.
    - M1.detects: with the `equivalence` row deleted from the canonical guidance table, the scenario failed with `tdd-strategy-guide: no selection row for equivalence in the guidance table.` (exit 1); the file was restored and `cmp` against the plugin copy matched.
    - M2: pass. `guidance-is-referenced-and-carries-no-criterion scenario passed.` with `ls src/skills/*/guidance.md` counting 2. With `An executor MUST x.` appended to the new guidance the same scenario failed naming `keel-tdd-or-test-first's guidance.md states a criterion — it contains 'MUST'`, so the rule reaches the new file; restored.
    - M3: pass. `native-plugin-manifests scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: an executor loading `keel-tdd-or-test-first` now reads that the strategy is chosen by what would make the Acceptance false and not by size, risk, model, or the cost of a red, and is pointed to a guidance table covering every strategy the parser accepts; `Detects:`, `Measured:`, `(regression)` with `deferred to C<n>`, and `artifact` are each stated in the body. The scenario derives the strategy list from the parser, so it fails when a strategy is added without a row.
      - Scope check: `git status --short` lists `README.md`, `scripts/validate_plugin.py`, both copies of the skill's `SKILL.md` and `guidance.md`, and this change's directory — all in Touch or the record layer. README and the validator comment are I1 and I2.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [ ] 2.1 Release and promote the spec
  - Covers:
    - E3
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
    - openspec/specs/keel-verification-layering/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the added requirement is promoted into `keel-verification-layering`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f386f19cc2ba95b613b7c93c2c8cb503bf0fc116542c6e73404b903f3df6d9c9 (keel 5.170.0)
    - M1: pending
    - M2: pending
    - M3: pending
    - Review: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "One skill is split today, `keel-run-single-task-goal`, and its body is 11% smaller for it. The other five are almost entirely criteria" — `README.md`, How much guidance the agent loads. Updated by: 1.1.
- I2: "D4 splits exactly one skill today." — the comment in `validate_guidance_is_referenced_and_carries_no_criterion_scenario`, `scripts/validate_plugin.py`. Updated by: 1.1.

## Expectation Coverage

- E1: An executor choosing a Verify strategy finds, in the skill it loads, how to choose by what would make the Acceptance false, with right and wrong examples, for every strategy the parser accepts (#389; D1, D2). Covered by: 1.1
- E2: `Detects:`, `Measured:`, `(regression)` with `deferred to C<n>`, and `artifact` are discoverable from that skill (#389; D1). Covered by: 1.1
- E3: The release carries it. Covered by: 2.1
- E4: Whether a strategy catches more defects is measured before any gate changes (#389 item 3; F2, D3). Durable owner: https://github.com/TanglmChris/keel/issues/411
