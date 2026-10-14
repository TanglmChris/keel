# Tasks

## 1. Desktop recipe

- [x] 1.1 The desktop recipe drops the dismiss step and the wake unarchives first
  - Covers:
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A desktop self-shift is told how its next session gets started
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A declared self-shift lets the session take the four steps without asking
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` follows the real `keel shift ready --wake` and `keel shift resume`. With the desktop variables, the output names `get_session`, `unarchive_session`, `mcp__ccd_session_mgmt__get_session` and `mcp__ccd_session_mgmt__unarchive_session`; `set_remote_control("self", false)` appears before `create_scheduled_task`, and `get_session` before `unarchive_session` before `send_message`; the output names neither `unbind_pr` nor `get_status` and does not contain `archived copy`. Without the variables, the output names none of `unbind_pr`, `get_session` and `unarchive_session`. Both shift-change docs name `get_session` and `unarchive_session` and neither names `unbind_pr`. Fails with: `unbind_pr`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario self-shift-authorization` passes, and the desktop output with `self-shift` declared says `take these four steps now`. Fails with: `four steps`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4aa2dfa5519803a3425c9e7fff6243d8d16a074d34e3f5e41f5b66f641a9d66c
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` reports `shift-desktop-wake scenario passed.`
    - M1.red: fail. With the scenario changed first, it reported `shift-desktop-wake: the desktop clear hint still names unbind_pr: …`, carrying the declared signature `unbind_pr`.
    - M1.green: pass. With the dismiss step removed, the task's prompt checking `get_session` then `unarchive_session` then `send_message`, the permission line naming `mcp__ccd_session_mgmt__get_session`, and both docs updated, the scenario passed; its non-desktop arm names none of `unbind_pr`, `get_session` and `unarchive_session`.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario self-shift-authorization` reports `self-shift-authorization scenario passed.`
    - M2.red: fail. It reported `self-shift-authorization: a desktop ready --wake with self-shift declared does not cover four steps: …`, carrying the declared signature `four steps`.
    - M2.green: pass. With the hint saying `take these four steps now`, the scenario passed.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenarios run the real `keel shift ready --wake` and `resume` with and without the desktop variables, and assert the absence of `unbind_pr` and `get_status`, the order `get_session` < `unarchive_session` < `send_message`, the permission names, the absence of "archived copy", and `four steps` under `self-shift`; the docs check forbids `unbind_pr` and requires `get_session` and `unarchive_session` in both languages.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `README.md`, `keel/config.yaml`, `scripts/validate_plugin.py`, and this change's directory.
      - Findings: the recipe itself cannot be proven by a scenario: whether `get_session` reports `isArchived` for an archived session and whether the unarchived session's next turn re-acquires its worktree are host facts, measured once (2026-10-14 15:52, #326 comment 6163730805) and owed a run on the next real desktop self-shift. Durable owner: https://github.com/TanglmChris/keel/issues/326
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
    - Contract: keel-task-capsule/v1 sha256:b36d533c95c5f62e0e8efd7fe39ba78c8165eabf875c760abcc2a156cd07f5a6
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.133.0; with the 5.133.0 changelog section written (and the stub section the bump inserted removed), `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. Both MODIFIED requirements replace their counterparts in `openspec/specs/keel-shift-change/spec.md` and `openspec/specs/keel-standing-authorization/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`, and `openspec validate shift-desktop-unarchive-wake --strict` reports the change valid.
    - Review:
      - Status: pass
      - Acceptance check: the two scenarios check the markers, the changelog, and both promoted specs; the full suite runs on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, both published specs, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "Dismiss every PR bound to this session", "take these five steps", "dismiss the PRs bound to it (#326)" and "the five steps `keel shift ready --wake` prints" — `src/core/shift.js`, `README.md`, the `keel/config.yaml` comment, `docs/shift-change.md` ("dismiss every PR bound to the session"), `docs/shift-change.zh-CN.md` ("解绑这个会话绑定的所有 PR", "交班前的五步"), and the `self-shift-authorization` scenario ("five steps"). Updated by: 1.1
- I2: "`mcp__ccd_pr__unbind_pr`" in the unattended permission list — `src/core/shift.js` and both shift-change docs. Updated by: 1.1
- I3: "It covers exactly the five steps" and "dismiss every PR bound to this session, reading them with `get_status`" — `openspec/specs/keel-standing-authorization/spec.md` and `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1
- I4: the 5.131.0 changelog entry "A desktop self-shift dismisses its bound PRs, so auto-archive leaves it for the wake". Discard reason: a released changelog entry records what that release did; the new entry states that the step did not hold and was removed.

## Expectation Coverage

- E1: A desktop self-shift's printed steps no longer claim that dismissing bound PRs keeps the session from auto-archive (D1). Covered by: 1.1
- E2: The wake unarchives an archived session before sending, so an archive in the gap costs nothing, and says which path it took (D2). Covered by: 1.1
- E3: The release carries it. Covered by: 2.1
- E4: The next desktop self-shift runs the new recipe end to end across a gap with an archive in it. Durable owner: https://github.com/TanglmChris/keel/issues/326
- E5: Turning Remote Control off can block for hours, which would stall an unattended shift at step 1. Durable owner: https://github.com/TanglmChris/keel/issues/324

## Change Evidence

- C1: pass. `npm test` on the 5.133.0 tree reports `validation --all passed: baseline plus 278 scenarios, 1 skipped: output-survives-the-pipe.`
