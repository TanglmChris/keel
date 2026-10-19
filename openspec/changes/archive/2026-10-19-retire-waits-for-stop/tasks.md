# Tasks

## 1. The rename waits for the stop

- [x] 1.1 Resume the old session for its rename only once `claude agents` shows it stopped
  - Covers:
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / The rename waits for the stop to take effect
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / A session that never stops is not resumed
    - D1
  - Read:
    - src/core/shift.js
    - openspec/changes/retire-waits-for-stop/design.md
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` with the fake `claude`'s `stop` taking effect two listings after it returns and a resume of a session still running starting a copy, as measured (F1): the `/rename` resume runs only after the old session lists as stopped, no copy is started, and the old session takes the shifted name. Fails with: `the rename resumed a session that was still running`
    - M2: the same scenario with a `stop` that never takes effect and `KEEL_SHIFT_STOP_WAIT_MS` short: no `/rename` resume runs, the new session still starts, and status says the rename was not shown. Fails with: `a session that never stopped was resumed for its rename`
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e1300c0e341fdaffd7799c68b85780ff47301fda1ab08cba1d97551e5fc3213f (keel 5.165.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` reports `shift-cli-self-shift scenario passed.`
    - M1.red: fail. With the fake's `stop` taking effect two listings late and the code unchanged: `shift-cli-self-shift: the rename resumed a session that was still running, starting a copy: [...]` — the original `verify` stopped with its old name, and a copy `c0c0c0c0` named `verify · shifted …` left with `status: idle`, the shape of the real keel-maint hand-over (F2).
    - M1.green: pass. With `retire()` polling `claude agents` after the stop until the row has no `status`, the resume ran on the stopped session, no copy was started, and it took the shifted name.
    - M2: pass. The never-stops section of the same scenario passes (no `--resume` call, one new session, status `delivered` with `rename not shown`).
    - M2.red: fail. With the main path's stop lag set to 0 (so the scenario reached this section) and the code unchanged: `shift-cli-self-shift: a session that never stopped was resumed for its rename: [['stop', '5b14fbae'], ['--bg', '--resume', '5b14fbae-…', '/rename verify · shifted 2026-10-19 21:38'], ['stop', '5b14fbae'], ['--bg', '-n', 'verify', …]]`; the scenario was restored afterwards.
    - M2.green: pass. With the bounded wait, a session still showing a status at `KEEL_SHIFT_STOP_WAIT_MS` is stopped again and not resumed, and the hand-over is delivered with the rename recorded as not shown.
    - M3: pass. `npm test`: `validation --all passed: baseline plus 305 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit. An earlier run failed `assertion-shape-count` (81 vs 80) on one `if` of the new section joining three failures behind one message; it was split into three, and the rerun passed.
    - Review:
      - Status: pass
      - Acceptance check: against a fake `claude` whose `stop` takes effect late and whose resume of a running session starts a copy (both as measured on Claude Code 2.1.303, F1), the hand-over resumes only a stopped session, leaves no copy, and renames the original; a session that never stops is not resumed and the hand-over still delivers.
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md` and this change's directory, all in Touch or the record layer.
      - Findings:
        - Durable owner: https://github.com/TanglmChris/keel/issues/395 — the next real CLI shift on 5.166.0 checks that the old session is renamed and no copy is left; its result is reported there.
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
    - Contract: keel-task-capsule/v1 sha256:0b76b667e0fdb3ac7c8bd19b40f602aaa20175dae7fc98e5089047c50c9594c7 (keel 5.165.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.165.0 → 5.166.0; with the "The CLI hand-over renames the old session only once it has stopped" section written into the stub the bump left, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirement was promoted into `keel-shift-change`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`claude stop` — which keeps the conversation — then a resume with `/rename <role> · shifted <date time>`" — `docs/cli-team.md` and its zh-CN twin, and the `retire()` comment in `src/core/shift.js`: true only once the stop has taken effect. Updated by: 1.1.
- I2: "stopping it with `claude stop`, keeping its conversation, renaming it" — the CLI requirement in `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1.

## Expectation Coverage

- E1: Retiring the old session leaves no running copy of it and renames the original (#395; D1). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
