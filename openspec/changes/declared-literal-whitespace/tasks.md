# Tasks

## 1. Whitespace-insensitive declared literals

- [x] 1.1 Compare declared literals with recorded Evidence with whitespace runs as one space
  - Covers:
    - keel-core-gates / Declared literals and recorded Evidence are compared with whitespace runs as one space / A literal with aligned spaces matches the raw output
    - keel-core-gates / Declared literals and recorded Evidence are compared with whitespace runs as one space / Different characters are still refused
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/declared-literal-whitespace/design.md
    - src/core/gates.js
    - src/core/task-contract.js
  - Touch:
    - src/core/gates.js
    - scripts/validation/contract.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario declared-literal-whitespace`: through the real `keel gate task-complete --json` on a vertical-tdd fixture, a check whose declared failure signature is `FAIL  record reachable` (two spaces) completes with `.red` Evidence quoting `FAIL  record reachable` (two spaces); a check whose declared injection failure is `FAIL  guard missing` completes with `.detects` Evidence quoting `FAIL   guard missing` (three spaces); a check whose declared measurement is `took  12 s` completes with `M1` Evidence quoting `took 12 s`; and `.red` Evidence quoting `FAIL record unreachable` is refused with `red-missing-declared-failure` and a message containing `as one space`. Fails with: `declared-literal-whitespace:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group contract --jobs 4` passes, `a-red-declares-what-it-proves` and the injection and measurement scenarios among them, and so does `--scenario assertion-shape-count`, run on its own.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1b920dcfbc74ca97f09c5096a5e842d5a181a7961c56c31b81984904b9bc82db (keel 5.207.0)
    - M1: pass. `declared-literal-whitespace scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `declared-literal-whitespace: an aligned failure signature copied from the raw output was refused; ['red-missing-declared-failure'] 'M1 declares that its red fails with `FAIL record reachable`, and the recorded M1.red Evidence does not contain that string. …` (exit 1). The declared two-space literal was compiled single-spaced and searched for in the raw two-space red.
    - M1.green: pass. `containsDeclared` in `src/core/gates.js` collapses every whitespace run to one space in the recorded Evidence and the literal, and folds nothing else. The `Fails with:`, `Detects:`, and `Measured:` comparisons all use it (D1). Each of their refusals ends with `Runs of whitespace are compared as one space, so spacing is not the cause.` (D2). The literal is still taken from the normalized check text (D3). A red quoting `FAIL record unreachable` is still refused as `red-missing-declared-failure`.
    - M2: pass. `validation --group contract passed: 80 scenarios.` (exit 0), `a-red-declares-what-it-proves` and the injection and measurement scenarios among them. `assertion-shape-count` passed on its own at 74 sites.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel gate task-complete`, a failure signature, an injection failure, and a measurement, each copied with runs of spaces, matched Evidence quoting the raw output. A red with different characters was refused, and the refusal said whitespace runs compare as one space.
      - Scope check: `git status --short` lists `src/core/gates.js`, `scripts/validation/contract.py`, `scripts/validation/registry.py`, and this change's directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations:
      - 2026-10-26: M2 names the existing scenario by its registered name, `a-red-declares-what-it-proves`, rather than `red-declares-what-it-proves`, which the registry does not know. The assertions are unchanged; task-start was re-run before any execution evidence was recorded.

## 2. Release

- [ ] 2.1 Release and promote the spec
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
    - openspec/specs/keel-core-gates/spec.md
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
    - M2: the delta is promoted into `keel-core-gates`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
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
    - Reauthorizations: none

## Invalidates

- I1: "`keel gate task-complete` then requires that string in the check's `.red` Evidence" — `AGENTS.md`, `assets/bootstrap/AGENTS.md`, and the "MUST require the check's `.red` Evidence to contain that literal string" requirement in `openspec/specs/keel-core-gates/spec.md`. Discard reason: still true; containment is unchanged except that whitespace runs compare as one space, which the added requirement states beside it.
- I2: "A literal the recorded output does not contain" — the `Measured:` requirement in `openspec/specs/keel-task-capsule/spec.md`. Discard reason: still true in the same sense as I1; the added `keel-core-gates` requirement names `Measured:` too.

## Expectation Coverage

- E1: A declared literal copied from tool output with aligned spaces matches the raw output it was copied from, while different characters are still refused and the refusal rules spacing out (D1, D2, D3) (#479). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
