# Tasks

## 1. Re-arm reminder

- [x] 1.1 `patrol:` reminds the bound role in `keel context`, the session projection, and `keel shift resume`
  - Covers:
    - keel-coordinator-patrol / The patrolling role is reminded to re-arm its schedule / A new shift of the coordinator is reminded
    - keel-coordinator-patrol / The patrolling role is reminded to re-arm its schedule / Other roles and broken declarations are quiet
    - D1
    - D2
    - F1
    - F2
    - F3
    - F4
  - Read:
    - src/core/config.js
    - src/core/context.js
    - src/core/shift.js
    - plugins/keel/scripts/session-start.js
  - Touch:
    - src/core/config.js
    - src/core/context.js
    - src/core/shift.js
    - plugins/keel/scripts/session-start.js
    - keel/config.yaml
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-rearm` declares `patrol:` with `role: iecc-pm` and `every: 30m` in a repository with `openspec/` and worktrees bound to `iecc-pm` and `rtl`, and requires: in `iecc-pm`, `keel context --json` carrying `patrol` `{role: iecc-pm, every: 30m}`, the real SessionStart hook naming `keel patrol` and `30m`, and `keel shift resume` (after `keel shift ready`) ending with the reminder; in `rtl`, none of them; and with `every: soon`, no `patrol` field and a warning naming `patrol`. Fails with: `patrol-rearm:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ad8917a397a4ea73090d08f3359db721bff2622dd93b85ed79c59fa9bb2a7b93
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-rearm` reports `patrol-rearm scenario passed.`
    - M1.red: fail. Before the change the scenario reported `patrol-rearm: the coordinator's context carries patrol None.`, carrying the declared signature `patrol-rearm:`.
    - M1.green: pass. With `readPatrolDeclaration` and `patrolReminder` in `src/core/config.js`, `patrol` set in `resolveContext`, the hook's line, and the reminder appended by `keel shift resume`, the `iecc-pm` worktree carries `{role: iecc-pm, every: 30m}`, its projection names `keel patrol` and `30m`, its resume ends with the reminder; `rtl` gets none; and `every: soon` gives no `patrol` and a warning naming `patrol`.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 258 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario commits a real declaration, binds two roles, runs a real `shift ready`/`resume`, and reads `keel context --json` and the shipped SessionStart hook in each worktree.
      - Scope check: `git status --short` lists `src/core/config.js`, `src/core/context.js`, `src/core/shift.js`, the session-start hook, `keel/config.yaml`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

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
    - openspec/specs/keel-coordinator-patrol/spec.md
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
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirement is appended to `openspec/specs/keel-coordinator-patrol/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:27e753cc8f9b69e6e8c54b4643b77eb824e261e3584effb0756bf8a5517cab08
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.112.0 on top of `main` at 5.111.0 (#285). With the 5.112.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-coordinator-patrol/spec.md`; `published-specs-validate-strictly` reports `34 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published spec carries the requirement with both scenarios, and the changelog names the issue, the decision, and that Keel still schedules nothing.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.112.0 reports `validation --all passed: baseline plus 258 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "Eleven independent declarations live here" — the header of `keel/config.yaml`, which gains `patrol`. Updated by: 1.1

## Expectation Coverage

- E1: A new shift of the patrolling role is told to re-create its patrol schedule, from Git-held declaration alone (D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
