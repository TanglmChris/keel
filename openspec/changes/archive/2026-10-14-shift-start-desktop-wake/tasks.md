# Tasks

## 1. Start on the desktop app

- [x] 1.1 `keel shift start` names the wake step for a desktop note
  - Covers:
    - keel-shift-change / The coordinator starts the new shift once its note waits / Start for a desktop note names the wake step
    - D1
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-start-desktop` writes `verify`'s note with `keel shift ready` under `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and `CLAUDE_CODE_HOST_SESSION_ID=local_test-320`, runs the real `keel shift start verify` from `rtl`, and asserts the start record reaches `dm-rtl--verify`, the output names `send_message`, `get_session`, `unarchive_session`, `local_test-320` and `keel shift resume` and has no `Woke`; then a note written outside the desktop app still prints `Woke`. Fails with: `does not name send_message`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-change` still passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f57ada5f0488279f438337a1ccd9b9cf328a488eaf54d8445c9465af50da7908
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-start-desktop` reports `shift-start-desktop scenario passed.`
    - M1.red: fail. With the scenario written first, it reported `shift-start-desktop: start for a desktop note does not name send_message: Woke verify to start its new shift (… in dm-rtl--verify).`, carrying the declared signature `does not name send_message`.
    - M1.green: pass. With `start()` reading `Desktop session:` from the note and the CLI printing the get_session / unarchive_session / send_message step instead of `Woke`, the scenario passed. Against the real paused probe session of #320, `keel shift start start-probe "probe only"` printed `Posted the start for start-probe … so this alone wakes nothing.` and `Wake it: call \`get_session\` on \`local_04ae73d4-…\` …`; the same `send_message` step, sent by hand at 22:53, resumed that session in 9 s (#320 comment 6171236953).
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-change` reports `shift-change scenario passed.`; `npm test`: baseline plus 281 scenarios passed, 1 skipped.
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `ready` on a simulated desktop and the real `start`, checks the record still arrives via `keel chat read`, that the output names the wake step and the session id and no longer says `Woke`, and that a non-desktop note still prints `Woke`. The step itself was proven on the live app by the #320 control.
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validate_plugin.py`, both shift-change docs, and this change's directory.
      - Findings: `keel shift status` still describes a desktop note's waiting role as woken only by `ready --wake` or typing, without the coordinator's send_message path. Discard reason: the shift feature is frozen to bug fixes (owner, 2026-10-14); that line is incomplete, not false.
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
    - M1: `node scripts/bump_version.js patch` moves every marker to the next patch version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the MODIFIED requirement replaces its counterpart in the published spec, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:7936e23a4b7b9baf763be1ba674049ab0d7cb0f4de0311f83ad1565d4bc6a8d7
    - M1: `node scripts/bump_version.js patch` moved every marker 5.136.0 → 5.136.1; with the "`keel shift start` no longer claims a desktop wake it cannot make" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the MODIFIED requirement replaced its published counterpart, adding the desktop scenario; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files are the version markers, `keel/CHANGELOG.md` and `openspec/specs/keel-shift-change/spec.md`, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "then wakes the cleared role" and "留下后唤醒清空后的会话" — the coordinator row of the command tables in `docs/shift-change.md` and `docs/shift-change.zh-CN.md`. Updated by: 1.1
- I2: "post in the direct group a message that wakes `<role>`" with no desktop exception — `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: On the desktop app, `keel shift start` does not claim a wake it cannot make, and names the step that does (D1). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
