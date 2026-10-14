# Tasks

## 1. Desktop recipe

- [x] 1.1 The desktop recipe keeps Remote Control on through the clear, and resume restores it only if it is off
  - Covers:
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A desktop self-shift is told how its next session gets started
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A declared self-shift lets the session take its outgoing steps without asking
    - keel-shift-change / The new shift resumes from the note / A resumed desktop shift is told to restore Remote Control
    - keel-standing-authorization / A session's own shift change on the desktop app is a named authorization / self-shift is accepted and listed
    - D1
    - D2
    - D3
    - D4
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
    - README.md
    - keel/config.yaml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` follows the real `keel shift ready --wake` and `keel shift resume`. With the desktop variables, the ready output does not contain `set_remote_control("self", false)` nor `cannot be cleared`, names `create_scheduled_task` before `set_session_title` before `clear_session`, and names `new address`; the desktop resume output names `get_session` and `set_remote_control`. Without the variables, ready names none of `send_message` and `create_scheduled_task` and resume names neither `set_remote_control` nor `set_session_title`. Neither shift-change doc contains `cannot be cleared`. Fails with: `set_remote_control("self", false)`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario self-shift-authorization` passes, and the desktop output with `self-shift` declared says `take these three steps now`. Fails with: `three steps`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8a9fb37bdba156e61b42fd69fdf1664141313c9f215ef8592a8d49983e556e55
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` reports `shift-desktop-wake scenario passed.`
    - M1.red: fail. With the scenario changed first, it reported `shift-desktop-wake: the desktop clear hint still says set_remote_control("self", false): …`, carrying the declared signature `set_remote_control("self", false)`.
    - M1.green: pass. With the Remote Control step and the "cannot be cleared" line removed, the hint saying Remote Control reconnects under a new address, the steps ordered task → rename → clear, resume checking `get_session` before `set_remote_control`, and both docs updated, the scenario passed; its non-desktop arm still names none of the desktop steps.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario self-shift-authorization` reports `self-shift-authorization scenario passed.`
    - M2.red: fail. It reported `self-shift-authorization: a desktop ready --wake with self-shift declared does not cover three steps: …`, carrying the declared signature `three steps`.
    - M2.green: pass. With the hint saying `take these three steps now`, the scenario passed.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenarios run the real `keel shift ready --wake` and `resume` with and without the desktop variables and assert the absence of `set_remote_control("self", false)` and `cannot be cleared`, the order `create_scheduled_task` < `set_session_title` < `clear_session`, the `new address` sentence, `get_session` and `set_remote_control` in the desktop resume, and `three steps` under `self-shift`; the docs check forbids `cannot be cleared` in both languages.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `README.md`, `keel/config.yaml`, `scripts/validate_plugin.py`, and this change's directory.
      - Findings: the premise is a host fact measured once by the owner (F2–F4); whether a session started by a partner's `send_message` also reconnects Remote Control (F5) is unmeasured, which is why resume checks before turning it on. Durable owner: https://github.com/TanglmChris/keel/issues/324
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the specs
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
    - openspec/specs/keel-standing-authorization/spec.md
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
    - M2: both MODIFIED requirements replace their counterparts in the published specs, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:fb6f0533446852e6c7f273d22636a1c99c29b182c81c9861473c0353a60c8ef2
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.134.0; with the 5.134.0 changelog section written (the stub section the bump inserted removed), `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The three MODIFIED requirements replace their counterparts in `openspec/specs/keel-shift-change/spec.md` and `openspec/specs/keel-standing-authorization/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`, and `openspec validate shift-desktop-keep-remote-control --strict` reports the change valid.
    - Review:
      - Status: pass
      - Acceptance check: the two scenarios check the markers, the changelog, and the promoted specs; the full suite runs on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, both published specs, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "A session serving Remote Control cannot be cleared: turn Remote Control off, clear, then turn it back on." — the clear hint in `src/core/shift.js` and `docs/shift-change.md`. Updated by: 1.1
- I2: "Turn Remote Control off with set_remote_control(\"self\", false)", "take these four steps", "the four steps `keel shift ready --wake` prints", "turn the session's own Remote Control off and wait", "four outgoing shift steps" — `src/core/shift.js`, `README.md`, both `keel/config.yaml` comments, both shift-change docs ("先关掉 Remote Control", "交班前的四步"), and the `self-shift-authorization` scenario. Updated by: 1.1
- I3: "a clear keeps neither Remote Control nor this session's title" — `resume` in `src/core/shift.js` and both shift-change docs. Updated by: 1.1
- I4: "turn Remote Control off and wait for that call to return", "these four steps", "because a clear there keeps neither" and "It covers exactly the four steps" — `openspec/specs/keel-shift-change/spec.md` and `openspec/specs/keel-standing-authorization/spec.md`. Updated by: 2.1
- I5: native memory `remote-control-drops-on-self-shift` ("Create the wake task only after Remote Control is off"). Discard reason: native memory is outside the repository; this session updates it when the release lands.

## Expectation Coverage

- E1: A desktop self-shift's printed steps need no person: no Remote Control step (D1, D2). Covered by: 1.1
- E2: The woken session restores Remote Control only when it is off, and still its title (D3). Covered by: 1.1
- E3: The release carries it. Covered by: 2.1
- E4: A real desktop self-shift runs the three-step recipe end to end, including whether a session woken by `send_message` comes back with Remote Control on (F5). Durable owner: https://github.com/TanglmChris/keel/issues/324

## Change Evidence

- C1: pass. `npm test` on the 5.134.0 tree reports `validation --all passed: baseline plus 278 scenarios, 1 skipped: output-survives-the-pipe.`
