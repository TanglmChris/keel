# Tasks

## 1. Desktop wake

- [x] 1.1 The desktop wake prompt confirms delivery and says what to do when it fails
  - Covers:
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A desktop self-shift is told how its next session gets started
    - D1
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` follows the real `keel shift ready --wake`; with the desktop variables the output names `delivered`, `PushNotification` and `WAKE FAILED` after `send_message`, and both shift-change docs name `PushNotification` and `WAKE FAILED`. Fails with: `PushNotification`
    - M2 (regression): the same scenario's existing checks (order, no Remote Control off, the non-desktop arm) still pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e24f2c482c4e1ece75ca42fd522fe5c1efd4a2c8b36215fe0d014eed1cf1ddaa
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` reports `shift-desktop-wake scenario passed.`
    - M1.red: fail. With the scenario changed first, it reported `shift-desktop-wake: the desktop wake does not say PushNotification after send_message`, carrying the declared signature `PushNotification`.
    - M1.green: pass. With the wake prompt in `src/core/shift.js` saying `delivered` or `queued` is a delivered wake and any other result after the retry calls `PushNotification` and starts the reply with `WAKE FAILED`, and both docs saying the same, the scenario passed.
    - M2: pass. The same run passed every earlier check of the scenario: task → rename → clear order, no `set_remote_control("self", false)`, `get_session` → `unarchive_session` → `send_message`, and the non-desktop arm naming none of the desktop steps.
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel shift ready --wake` with the desktop variables and asserts `PushNotification`, `WAKE FAILED` and `delivered` appear after `send_message`, and both docs name the first two.
      - Scope check: `git status --short` lists `src/core/shift.js`, both shift-change docs, `scripts/validate_plugin.py`, and this change's directory.
      - Findings: whether the host's `send_message` really returns a non-delivered result for a session that fails to start is a host fact not measured here; the prompt covers it by treating anything but `delivered`/`queued` as failure. Durable owner: https://github.com/TanglmChris/keel/issues/326
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 `keel shift status` flags an overdue desktop wake
  - Covers:
    - keel-shift-change / Shift state is visible / An overdue desktop wake is flagged
    - D2
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake-overdue` runs the real `keel shift ready --wake` with the desktop variables, then `keel shift status` with `KEEL_SHIFT_WAKE_OVERDUE_MS` far away (no `overdue`) and at 0 (says `overdue` and names `local_test-319`, `list_task_runs` and `send_message`); a note written without the desktop variables at 0 does not say `overdue`; both shift-change docs name `overdue` (zh: `超时`). Fails with: `overdue`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:76db1e55a26b51fc93c5ec1d910355fd0881edc5cc168b087b8407494fff1503
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake-overdue` reports `shift-desktop-wake-overdue scenario passed.`
    - M1.red: fail. With the scenario written first, it reported `shift-desktop-wake-overdue: status past the overdue time does not name overdue`, carrying the declared signature `overdue`.
    - M1.green: pass. With `status` reading `Desktop session:` from a waiting note and `describe` adding the overdue line past `KEEL_SHIFT_WAKE_OVERDUE_MS` (default 15 min; zero accepted, which the shared `envMs` would have refused), and both docs' status rows updated, the scenario passed.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 279 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `ready --wake` and `status`: no `overdue` with the time far away; `overdue`, `local_test-319`, `list_task_runs`, `send_message` at 0; no `overdue` for a note without a desktop session; both docs name it.
      - Scope check: `git status --short` lists `src/core/shift.js`, both shift-change docs, `scripts/validate_plugin.py`, and this change's directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E3
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: both MODIFIED requirements replace their counterparts in the published spec, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3d5841f2d824a2338cac4f3e01eddd142a5b504f294044505a446b31995a6116
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.135.0; with the 5.135.0 changelog section written in place of the stub, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. Both MODIFIED requirements replace their counterparts in `openspec/specs/keel-shift-change/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the two scenarios check the markers, the changelog, and the promoted spec; the land job's full gate runs the suite on the bumped tree.
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the published spec, and the files 1.1 and 1.2 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "If that send is still refused because the session is archived, it unarchives it and sends once more, and it says which path it took." — the wake prompt in `src/core/shift.js`; "发送仍因已归档被拒时，再解除归档、重发一次" in `docs/shift-change.zh-CN.md` and its English counterpart in `docs/shift-change.md`: they stop at the retry and say nothing about a send that still fails. Updated by: 1.1
- I2: "Each role's state: requested, note waiting, or resumed." and "各角色的状态：已请求、便条等待中、已接班。" — the status row of both shift-change docs. Updated by: 1.2
- I3: "and, if that send is still refused because the session is archived, unarchives it and sends once more, saying which path it took;" and "`keel shift status` MUST list … with times." — `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1
- I4: "the `unarchive_session` fallback is what actually works" — native memory `desktop-auto-archive-eats-self-shift`, which predates the wake's delivery check and the 2026-10-14 18:00 run. Discard reason: native memory is outside the repository; this session updates it when the release lands.

## Expectation Coverage

- E1: A wake whose send does not deliver tells the owner instead of failing silently (D1). Covered by: 1.1
- E2: A wake that never ran is visible from `keel shift status` (D2). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1
- E4: Repeat the desktop self-shift end to end with a long gap and with the app in the background (D3). Durable owner: https://github.com/TanglmChris/keel/issues/326
- E5: Self-shift on Codex is unverified (parked by the owner). Durable owner: https://github.com/TanglmChris/keel/issues/334
