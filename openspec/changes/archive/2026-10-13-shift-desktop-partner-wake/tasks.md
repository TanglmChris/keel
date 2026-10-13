# Tasks

## 1. Desktop partner wake

- [x] 1.1 `ready --wake` and `resume` on the desktop app print the partner recipe and the Remote Control step
  - Covers:
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A desktop self-shift is told how its next session gets started
    - keel-shift-change / The new shift resumes from the note / A resumed desktop shift is told to restore Remote Control
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - F1
    - F4
  - Read:
    - src/core/shift.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/shift.js
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` follows the scenario through the real `keel shift ready --wake` and `keel shift resume`. With `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and `CLAUDE_CODE_HOST_SESSION_ID=local_test-319`, the note records `Desktop session: local_test-319`; the output names `create_scheduled_task`, `send_message`, `local_test-319`, `set_remote_control` and `mcp__ccd_session_mgmt__set_remote_control`, and lacks `The wake is armed`; and `resume` names `set_remote_control`. Without those variables, the output says `The wake is armed`, names neither `send_message` nor `create_scheduled_task`, and `resume` lacks `set_remote_control`. Both shift-change docs name `send_message` and `set_remote_control`. Fails with: `shift-desktop-wake:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:23e1928cfc94233d6d0ddce4b0712b6b0325f018a75d08a2f28823e04c581304
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` reports `shift-desktop-wake scenario passed.`
    - M1.red: fail. With the scenario written first and `src/core/shift.js` unchanged, it reported `shift-desktop-wake: the note does not record the desktop session id.`, carrying the declared signature `shift-desktop-wake:`.
    - M1.green: pass. With `desktopSession()`, the `Desktop session:` note line, the desktop clear hint, and the Remote Control line in `resume`, the behavior arm passed; the next run stopped at `shift-desktop-wake: docs/shift-change.md does not name send_message for the desktop app.`, and with both docs updated the scenario passed. The non-desktop arm (same worktree, variables absent) still says `The wake is armed`, names neither `send_message` nor `create_scheduled_task`, and its `resume` lacks `set_remote_control`.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 275 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real `keel shift ready --wake` and `keel shift resume` in a temporary repository bound to role `verify`, once with `CLAUDE_CODE_ENTRYPOINT=claude-desktop` and `CLAUDE_CODE_HOST_SESSION_ID=local_test-319` and once without, and reads the stored note, stdout, and both docs.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, and this change's own directory. `chat_environment` now also strips the two desktop variables (D5), so running the suite inside the desktop app does not change what the existing shift scenarios see.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/320 — a coordinator's `keel shift start` for a role cleared on the desktop app may wake nothing, for the same reason; this change records the session id it would need but leaves `start` unchanged.
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: both MODIFIED requirements replace their counterparts in `openspec/specs/keel-shift-change/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4260090b36776389a8e0a86a5270ca5b95a4c9207f409045fc1cc4b3268c772b
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.127.0; with the 5.127.0 changelog section written into the stub's place, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. Both MODIFIED requirements replace their counterparts in `openspec/specs/keel-shift-change/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the two scenarios check the version markers, the changelog section, and the promoted spec, and the full suite runs on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the published spec, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "The wake is armed: once …'s next session starts (after a clear or a fresh start), it gets one message to run `keel shift resume`." — the clear hint in `src/core/shift.js`, false on the desktop app. Updated by: 1.1
- I2: "On Claude that message wakes the new session like any other." — `docs/shift-change.md` `--wake` paragraph, and its translation in `docs/shift-change.zh-CN.md`. Updated by: 1.1
- I3: "MUST store the note and leave a detached one-shot waiter" with no host exception — `openspec/specs/keel-shift-change/spec.md`, A session changes its own shift and is woken once its next session starts. Updated by: 2.1
- I4: "the design must include this step in the recipe it prints" — native memory `remote-control-drops-on-self-shift`, an open design note that this change completes. Discard reason: native memory is outside the repository; the owner session updates it when this change lands.

## Expectation Coverage

- E1: A self-shift on the desktop app is told, before it clears, how its next session gets started without a human, and the resumed shift is told to restore Remote Control (D1–D6). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
- E3: A coordinator's `keel shift start` for a role cleared on the desktop app. Durable owner: https://github.com/TanglmChris/keel/issues/320

## Change Evidence

- C1: pass. `npm test` on the 5.127.0 tree reports `validation --all passed: baseline plus 275 scenarios, 1 skipped: output-survives-the-pipe.`
