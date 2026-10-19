# Tasks

## 1. A patrol recommends its next run

- [x] 1.1 Add the next-run recommendation and the adaptive cadence keys
  - Covers:
    - keel-coordinator-patrol / A patrol recommends its next run / Each rule is chosen by its own condition
    - D1
    - D2
    - D3
    - D4
  - Read:
    - src/core/patrol.js
    - src/core/config.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/patrol.js
    - src/core/config.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-next` runs the real `keel patrol --json` as coordinator `rtl` on a two-role repository: `fixed` at 3600 s without `cadence: adaptive`; with it, `idle` at 10800 s, `busy` at 3600 s after `verify`'s SessionStart, `quota` at 14400 s on a second `--quota 92`, `risk` at 1800 s after an uncommitted file under `--since-last`, `night` ending within the configured `quiet:` window, and `busy` raised to 3000 s by `min: 50m`, printed as `next: 50m (busy)`. Fails with: `next_rule None, not 'fixed'`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f0849fe657f507d75af2504a04266cc5d00bf8b8e30d31435f09918b1c360799 (keel 5.152.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-next` reports `patrol-next scenario passed.`
    - M1.red: fail. With the scenario written first and the code unchanged: `patrol-next: fixed: next_rule None, not 'fixed': {...}`, carrying the declared signature.
    - M1.green: pass. With `readPatrolDeclaration` reading `cadence`, the rule overrides, `quiet`, `min` and `max`, and `recommendNext` choosing risk, quota, night, busy or idle (or `fixed` at `every:`), printed as `next: <duration> (<rule>)`, carried as `next_after_s`/`next_rule`/`next_at` and logged as `next=`, the scenario passed.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 297 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: the real `keel patrol --json` gives `fixed` at 3600 s without `cadence: adaptive`, then `idle` 10800 s, `busy` 3600 s once `verify`'s session starts, `quota` 14400 s on a repeated `--quota 92`, `risk` 1800 s when a committed clean checkout gains a file, `night` ending inside the `quiet:` window, and `busy` raised to 3000 s by `min: 50m`, printed and logged as `next: 50m (busy)`.
      - Scope check: `git status --short` lists `src/core/patrol.js`, `src/core/config.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Durable owner: https://github.com/TanglmChris/keel/issues/356 — the issue's re-arming task and its `runner` declaration are left to the owner's CLI waker (`keel tick`), the next change; this change only recommends.
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta requirements are promoted into `keel-coordinator-patrol`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:755bfe906eaa3d5074517ab0982efcf8d9b3b5895e470bb600d314a080125269 (keel 5.152.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.152.0 → 5.153.0; with the "A patrol recommends its next run" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-coordinator-patrol`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: A patrol says when it should run next, by a rule the owner can tune, so a runner need not run it hourly regardless (#356, D1, D2, D3, D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
