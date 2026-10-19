# Tasks

## 1. The hand-over waits on the session's status

- [x] 1.1 Decide finished on `status` alone, and make the scenario use the measured shapes
  - Covers:
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / The waker hands a CLI shift over once the old session is idle
    - D1
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` with the fake `claude` answering busy, then `status: waiting` / `state: blocked` (the measured question shape), then `status: idle` / `state: working` (the measured shape of keel-maint's ended turn), and no tick: nothing is stopped or started while busy or waiting, and the waiter retires the old session and starts the new one once it is idle. Fails with: `the waiter did not hand over without a tick`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:973860dc99fa763d568bb53e0e383ac3ca038bbfeabe06b3f4916eb91adc9fc1 (keel 5.164.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` reports `shift-cli-self-shift scenario passed.`
    - M1.red: fail. With the scenario switched to the measured shapes and the code unchanged: `shift-cli-self-shift: the waiter did not hand over without a tick: []`, carrying the declared signature — the same failure as the owner's end-to-end test, an ended turn whose state still reads `working`.
    - M1.green: pass. With `finished()` deciding on `status` alone (absent row or status, or `idle`), the scenario passed: busy and `waiting`/`blocked` were left alone, and the `idle`/`working` session was retired and replaced by the waiter with no tick.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 305 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: against a fake `claude` answering with the two shapes measured on 2026-10-19 (a question: `status: waiting`, `state: blocked`; keel-maint's ended turn: `status: idle`, `state: working`), the waiter waits on the first and hands over on the second.
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md` and this change's directory, all in Touch or the record layer.
      - Findings:
        - Durable owner: https://github.com/TanglmChris/keel/issues/393 — the real end-to-end shift is re-run once 5.165.0 is installed; its result is reported there.
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
    - openspec/specs/keel-shift-change/spec.md
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
    - M2: the delta requirements are promoted into `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bf77c0ae117327e500189356f8b1fbb0e8fe9e79a18430fecc047b251739e63b (keel 5.164.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.164.0 → 5.165.0; with the "The CLI hand-over waits on the session's status, not its job state" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-shift-change`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "or its job state is still `working` — it is blocked on a question to you" — `docs/cli-team.md` and its zh-CN twin, and the `finished()` comment in `src/core/shift.js`. Updated by: 1.1.
- I2: "its job state is neither done nor idle, such as a session blocked on a question" — the CLI requirement in `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1.

## Expectation Coverage

- E1: A CLI session that has ended its turn is handed over whatever its last message said, and one waiting on the owner is not (#393; D1). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
