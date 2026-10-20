# Tasks

## 1. The new session is named for its start

- [x] 1.1 Start the new session as `<role> · <MM-DD HH:MM>` and stop resuming the old one
  - Covers:
    - keel-shift-change / A CLI session changes its own shift and the next one is named for its start / The waker hands a CLI shift over once the old session is idle
    - D1
    - D2
  - Read:
    - src/core/shift.js
    - openspec/changes/shift-session-names/design.md
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift`: once the old session is idle the calls are exactly `stop 5b14fbae` and `--bg -n "verify · <MM-DD HH:MM>" --permission-mode auto …` with no `--resume` of the old session, and `keel shift status` shows the delivered hand-off with that name. Fails with: `the hand-over woke the old session to rename it`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0a0fc799a9b12143ea52d96dbb272c74c8e3cbaad684feb6e7c6e63630454cfc (keel 5.166.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` reports `shift-cli-self-shift scenario passed.`: once the old session was idle the calls were `stop 5b14fbae` and `--bg -n "verify · 10-20 07:5x" --permission-mode auto …`, with no `--resume`; status showed the delivered hand-off with that name.
    - M1.red: fail. With the scenario expecting no resume and 5.167.0's code: `shift-cli-self-shift: the hand-over woke the old session to rename it: [['stop', '5b14fbae'], ['--bg', '--resume', '5b14fbae-…', '/rename verify · shifted 2026-10-20 07:54'], ['stop', '5b14fbae'], ['--bg', '-n', 'verify', …]]`.
    - M1.green: pass. With `retire()` reduced to `claude stop` and the new session started with `-n` from `sessionName()` (role plus local `MM-DD HH:MM`), recorded as `new_name`, the scenario passed; `shift-cli-keeps-old-sessions`, `shift-slash-command` and `assertion-shape-count` pass too.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 307 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: through `keel shift ready --wake` and the waiter against a fake `claude`, the old session is stopped and never resumed, and the new one starts under a name made of the role and its start time; status shows that name. Whether claude.ai shows it is the real shift's to confirm.
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md` and this change's directory, all in Touch or the record layer.
      - Findings:
        - Durable owner: https://github.com/TanglmChris/keel/issues/399 — the end-to-end shift on this release checks the new session's name in `claude agents` and that the old one is not woken; sessions started before this release keep the bare role name until `keep_old_sessions` removes them.
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
    - Contract: keel-task-capsule/v1 sha256:3e5c5a4d12fdd8a97e3f0f9ec0c01d1a6fd875f7e48519e6e92d7c7b064c8076 (keel 5.166.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.167.0 → 5.168.0; with the "The CLI hand-over names the new session for its start" section written into the stub the bump left, `version-alignment scenario passed.` (exit 0).
    - M2: the ADDED requirement replaced the REMOVED one in place in `keel-shift-change`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "a waiter stops and renames the old session" and "a resume with `/rename <role> · shifted <date time>`" — `docs/cli-team.md` and its zh-CN twin (the table row and the hand-over paragraph), and "a waiter stops it and renames it" in the `ready` output in `src/core/shift.js`. Updated by: 1.1.
- I2: "renaming it `<role> · shifted <date time>` by resuming it" — the CLI requirement in `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1.

## Expectation Coverage

- E1: Each shift's session has a name of its own in the owner's agent list, and the old session is not woken to get one (#399; D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
