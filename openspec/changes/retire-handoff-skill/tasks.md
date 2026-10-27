# Tasks

## 1. Retire the handoff skill

- [x] 1.1 Remove the handoff skill, and document the HANDOFF format in `keel --help` and the README
  - Covers:
    - keel-native-plugin-package / The slash menu offers what a person runs / The plugin ships the renamed skills and the new commands
    - keel-native-plugin-package / The review checklist loads its conditional checks on demand / The base checklist names the conditions and not their criteria
    - keel-stateless-continuity / The HANDOFF format is documented without a skill / Help names the fields and the actions
    - D1
    - D2
    - D3
    - D4
  - Read:
    - openspec/changes/retire-handoff-skill/design.md
    - plugins/keel/skills/handoff/SKILL.md
    - bin/keel.js
    - scripts/validation/hosts.py
    - scripts/validation/contract.py
    - scripts/validation/docs.py
  - Touch:
    - plugins/keel/skills/handoff/SKILL.md
    - src/skills/handoff/SKILL.md
    - bin/keel.js
    - plugins/keel/.codex-plugin/plugin.json
    - docs/commands.md
    - docs/commands.zh-CN.md
    - README.md
    - README.zh-CN.md
    - scripts/validation/hosts.py
    - scripts/validation/baseline.py
    - scripts/validation/common.py
    - scripts/validation/contract.py
    - scripts/validation/docs.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario slash-menu-ships`: the packaged plugin's skills are exactly `align-expectations`, `debug-failure`, `review-checklist`, and `tdd-or-test-first`, with no `handoff`, and `docs/commands.md` and its zh-CN copy list every person-invocable skill and no other. Fails with: `slash-menu-ships:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario handoff-format-in-help`: the real `keel --help` output names `keel-handoff/v1`, `owner`, `action`, `reason`, `discuss`, `author`, `task-start`, `task-complete`, and `change-close`, and both READMEs name `keel-handoff/v1` and each of the five actions. Fails with: `handoff-format-in-help:`
    - M3 (regression): run one at a time, each passes: `--scenario review-checklist-conditional-checks`, `--scenario expectation-completion-gates`, `--scenario uninstall`, `--scenario readme-zh-matches-english`, `--scenario surfaces-agree-with-code`, `--scenario assertion-shape-count`, and the baseline, `node scripts/run_python.js scripts/validate_plugin.py` with no argument, which reads `CORE_KEEL_SKILLS` and `SKILL_DOC_REQUIREMENTS`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9e380b623e4570ecbce7a442cbe0c1e1e9a9715bda929c23022de89de6ec46d6 (keel 5.209.0)
    - M1: pass. `slash-menu-ships scenario passed.` (exit 0).
    - M1.red: fail. With the test expecting four skills and the plugin unchanged: `slash-menu-ships: the plugin's skills are ['align-expectations', 'debug-failure', 'handoff', 'review-checklist', 'tdd-or-test-first'], not ['align-expectations', 'debug-failure', 'review-checklist', 'tdd-or-test-first'].` (exit 1).
    - M1.green: pass. `plugins/keel/skills/handoff/` and `src/skills/handoff/` are deleted, `KEEL_SKILLS` in `bin/keel.js` drops `handoff`, the Codex plugin's `longDescription` drops "and handoff hygiene", and both command lists drop the `/keel:handoff` row (D1). `slash-menu-ships` now also refuses a `/keel:<name>` in either list that a person cannot invoke.
    - M2: pass. `handoff-format-in-help scenario passed.` (exit 0).
    - M2.red: fail. Before the help text changed: `handoff-format-in-help: keel --help's Project layout does not name 'owner': '\n  continuity is recomputed from OpenSpec on every invocation.\n  keel/HANDOFF.md is an optional keel-handoff/v1 pointer override.\n …'` (exit 1).
    - M2.green: pass. `keel --help`'s Project layout states the YAML front matter: `schema: keel-handoff/v1`, `owner` (a pointer into `openspec/changes/<change>/`), `action` with its five values, `reason`, and no other field, and that `keel context --clear-handoff` removes it. Both READMEs open `## Commands` with the same paragraph (D2).
    - M3: pass. Run one at a time, each exit 0: `review-checklist-conditional-checks scenario passed: the base checklist is 79 lines.`, `expectation-completion-gates scenario passed.`, `uninstall scenario passed.`, `readme-zh-matches-english scenario passed.`, `surfaces-agree-with-code scenario passed.`, `assertion-shape-count scenario passed: 74 sites`, and the no-argument baseline `Keel v4.1.0 baseline validation passed.`. `review-checklist-conditional-checks` now reads `docs/shift-change.md` for the shift-note/HANDOFF distinction (D3); `CORE_KEEL_SKILLS`, `PLUGIN_SKILLS`, and `SKILL_DOC_REQUIREMENTS` drop the skill, and `expectation-completion-gates` checks the format snippets in `bin/keel.js` (D4).
    - Review:
      - Status: pass
      - Acceptance check: the packaged plugin ships exactly four skills with no `handoff`, and neither command list names `/keel:handoff` (M1); the real `keel --help` and both READMEs name `keel-handoff/v1`, the fields, and the five actions (M2); `keel context`'s HANDOFF handling is untouched (`src/core/context.js` unchanged).
      - Scope check: `git status --short` lists the two deleted skill files, `bin/keel.js`, the Codex plugin manifest, both command lists, both READMEs, `scripts/validation/` `baseline.py`, `common.py`, `contract.py`, `docs.py`, `hosts.py`, and `registry.py`, and this change's directory, all in Touch; `.DS_Store` was untracked before.
      - Findings: Resolved here: M3 — the `review-checklist-conditional-checks` docstring still said the handoff skill tells the override apart; it now names `docs/shift-change.md`, and the old-name pattern in `hosts.py` dropped a `handoff` exclusion that no longer applies.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [ ] 2.1 Release and promote the specs
  - Covers:
    - E2
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-native-plugin-package/spec.md
    - openspec/specs/keel-stateless-continuity/spec.md
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
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the deltas are promoted into `keel-native-plugin-package` and `keel-stateless-continuity`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract:
    - M1:
    - M2:
    - M3:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`align-expectations` and `handoff` MUST stay user-invocable" and "the skills are exactly the five names" — the requirement "The slash menu offers what a person runs" in `openspec/specs/keel-native-plugin-package/spec.md`. Updated by: 2.1.
- I2: "The handoff skill MUST tell the HANDOFF override apart from the shift note" — the requirement "The review checklist loads its conditional checks on demand" in the same spec. Updated by: 2.1.
- I3: "`/keel:handoff [create, validate, or clear]`" — `docs/commands.md` and its row in `docs/commands.zh-CN.md`. Updated by: 1.1.
- I4: "and handoff hygiene" — the `longDescription` in `plugins/keel/.codex-plugin/plugin.json`. Updated by: 1.1.
- I5: "keel/HANDOFF.md is an optional keel-handoff/v1 pointer override." — the Project layout section of `keel --help` in `bin/keel.js`, which names no field. Updated by: 1.1.

## Expectation Coverage

- E1: The `handoff` skill is gone from the plugin and its lists, the HANDOFF override still works, and its format stays documented in `keel --help` and the README (D1–D4) (#485). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
