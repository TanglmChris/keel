# Tasks

## 1. dsh's sandbox as measured

- [x] 1.1 The catalog shows dsh's own sandbox and corrected pitfalls, and a `{tmp}` template points temporary files beside the brief
  - Covers:
    - keel-external-agents / The external agent catalog records facts and is read on demand / dsh's own sandbox is described
    - keel-external-agents / The external agent brief is the delegation brief, checked for egress / A dsh brief points temporary files beside the brief
    - D1
    - D2
    - D3
    - F1
    - F2
    - F3
    - F4
    - I1
  - Read:
    - src/core/agents.js
  - Touch:
    - src/core/agents.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario external-agent-catalog` requires `keel agents dsh` to print a Sandbox line naming `workspace-write`, pitfalls naming `/dev/stdout` and `PYTHONPYCACHEPREFIX`, and no `reads and writes wherever it is started`. Fails with: `external-agent-catalog:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario external-agent-brief` requires the `dsh` helper brief over a separate worktree to create `tmp` beside `--out`, name it in the brief, and print a command setting `TMPDIR` to it and `PYTHONPYCACHEPREFIX` to its `pycache`. Fails with: `external-agent-brief:`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8a59e46e4b8c61e8d19353e81cb1668d029d9f7decc3c59dee961ad0b5300a13
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario external-agent-catalog` reports `external-agent-catalog scenario passed.`
    - M1.red: fail. Before the change the scenario reported `external-agent-catalog: \`keel agents dsh\` does not describe its own sandbox: 'Sandbox: helper none (needs a separate worktree); implementation none (needs a separate worktree)'`, carrying the declared signature `external-agent-catalog:`.
    - M1.green: pass. With `ownSandbox` on dsh's entry and printed on the Sandbox line, the no-sandbox pitfall replaced, and the `/dev/stdout` and `PYTHONPYCACHEPREFIX` pitfalls added, the scenario passes. `ownSandbox` joined the scenario's fact-field set, since it records a measured fact, not a judgement of what dsh suits.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario external-agent-brief` reports `external-agent-brief scenario passed.`
    - M2.red: fail. Before the change the scenario reported `external-agent-brief: the dsh brief did not create …/tmp beside --out.`, carrying the declared signature `external-agent-brief:`.
    - M2.green: pass. With `{tmp}` filled by a `tmp` directory created beside `--out` and named in the brief, and dsh's template setting `TMPDIR` and `PYTHONPYCACHEPREFIX`, the scenario passes; `external-agent-exit-status` and `external-agents-are-documented` still pass.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: both scenarios drive the real CLI: `keel agents dsh` output is read line by line, and the brief's directory, prompt text, and printed command are checked for the temporary directory.
      - Scope check: `git status --short` lists `src/core/agents.js`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: the facts are the reporter's measurement on dsh 0.2.0-rc.2 and are stamped with it; no dsh run was repeated here, because a run sends the brief to DeepSeek and the issue's record is specific.

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E2
    - I2
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
    - openspec/specs/keel-external-agents/spec.md
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
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-external-agents/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:885ba5f926175628663a86dfa523fad654df755c5a50b4f493f3b8b6f32fedbb
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. After merging `main` (5.99.4, #265), `node scripts/bump_version.js patch` moved every marker to 5.99.5. With the 5.99.5 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The three MODIFIED requirements replace their published copies, keeping their scenarios and adding two; the write-boundary scenario now reads "which offers no read-only sandbox" (I2). `published-specs-validate-strictly` reports `31 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published requirements carry `ownSandbox` and `{tmp}` with their scenarios, the no-sandbox wording is gone from the spec, and the changelog names the issue and the measurement.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after merging `main` and the bump to 5.99.5 reports `validation --all passed: baseline plus 239 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "It offers no sandbox flag and no working-directory flag. It reads and writes wherever it is started" — dsh's pitfall in `src/core/agents.js`. Updated by: 1.1
- I2: "a helper brief for `dsh`, which offers no sandbox" — the write-boundary requirement's scenario in `openspec/specs/keel-external-agents/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: The catalog describes dsh's sandbox as measured, and a dsh brief keeps temporary files beside the brief (D1, D2, D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
