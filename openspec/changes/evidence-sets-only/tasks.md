# Tasks

## 1. Count a stand-in only where it is set

- [x] 1.1 Match each marker only where the code sets it
  - Covers:
    - keel-validation-runner / The suite states what kind of evidence ran / A scenario that only removes host variables is deterministic
    - D1
    - D2
  - Read:
    - openspec/changes/evidence-sets-only/design.md
    - scripts/validation/evidence.py
  - Touch:
    - scripts/validation/evidence.py
    - scripts/validation/selfcheck.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario release-evidence-classes` passes with a new assertion that `chat-core` is listed as deterministic. Its existing assertions also hold: `shift-cli-self-shift`, `chat-claude-hooks`, `codex-receiving` and `update-pack-install` are listed as stand-in host, and the two classes cover the registry. Fails with: `release-evidence-classes: chat-core`
    - M2 (regression): the baseline, `--group selfcheck`, `--group docs` and `--scenario assertion-shape-count` pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9027a375b383ae8417f6794e134daa3646471a39f60f0dcb1f13186683d77907 (keel 5.187.0)
    - M1: pass. `release-evidence-classes scenario passed: 218 deterministic, 100 stand-in host.` `chat-core` is now deterministic. `shift-cli-self-shift`, `chat-claude-hooks`, `codex-receiving` and `update-pack-install` stay stand-in host, and the classes still cover the registry.
    - M1.red: `release-evidence-classes: chat-core is counted as run against a stand-in host for removing host variables.` This ran on the 5.187.0 classifier, which counted a marker wherever it was mentioned.
    - M1.green: `release-evidence-classes scenario passed: 218 deterministic, 100 stand-in host.` `evidence.sets()` matches a marker only in one of these forms: a dict key, an item assignment, `NAME=`, or an attribute assignment. `classify()` uses those matchers in place of the plain text test.
    - M2: pass. The baseline exits 0, and `assertion-shape-count` still has 74 sites. Both groups report their evidence lines:
      - `--group selfcheck`: `validation --group selfcheck passed: 9 scenarios, 1 skipped: output-survives-the-pipe.`, then `evidence: 9 deterministic, 0 against a stand-in host, …`.
      - `--group docs`: `validation --group docs passed: 22 scenarios.`, then `evidence: 22 deterministic, 0 against a stand-in host, …`.
    - Review:
      - Status: pass
      - Acceptance check: M1 asserts both directions through `--evidence`. A scenario that only strips host variables, `chat-core`, is deterministic. Scenarios that set an override, set a host data directory, send a hook payload, call a delegated script or put a program on PATH all stay stand-in host.
      - Scope check: the changes are `scripts/validation/evidence.py` and one assertion in `scripts/validation/selfcheck.py`, plus this change's record.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

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
    - openspec/specs/keel-validation-runner/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-validation-runner`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
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

- I1: In the 5.186.0 changelog, `evidence: 181 deterministic, 136 against a stand-in host` and "A scenario counts as stand-in host when the markers appear in its own code". Discard reason: a changelog entry records what that release did, and 5.188.0's entry states the change.

## Expectation Coverage

- E1: The evidence counts no longer count a scenario as stand-in host for removing or reading a host variable (D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
