# Tasks

## 1. Desktop recipe

- [x] 1.1 The desktop recipe dismisses this session's bound PRs before the task, drops "archived copy", and the wake falls back to unarchive
  - Covers:
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A desktop self-shift is told how its next session gets started
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A declared self-shift lets the session take the five steps without asking
    - keel-standing-authorization / A session's own shift change on the desktop app is a named authorization / self-shift is accepted and listed
    - D1
    - D2
    - D3
    - D4
    - D5
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` follows the real `keel shift ready --wake` and `keel shift resume`. With the desktop variables, the output names `get_status`, `unbind_pr`, `unarchive_session`, `mcp__ccd_pr__unbind_pr` and `mcp__ccd_session_mgmt__unarchive_session`; `set_remote_control("self", false)` appears before `unbind_pr`, and `unbind_pr` before `create_scheduled_task`; the output does not contain `archived copy`. Without the variables, the output names none of `unbind_pr` and `unarchive_session`. Both shift-change docs name `unbind_pr` and `unarchive_session`. Fails with: `unbind_pr`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario self-shift-authorization` passes, and the desktop output with `self-shift` declared says `take these five steps now`. Fails with: `five steps`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6c81600ada245c364733d8f547e7059797dd0ddeff59ab9d4c21f8fcab46d4e6
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` reports `shift-desktop-wake scenario passed.`
    - M1.red: fail. With the scenario extended first, it reported `shift-desktop-wake: the desktop clear hint does not name unbind_pr: …`, carrying the declared signature `unbind_pr`.
    - M1.green: pass. With step 2 (dismiss bound PRs), the unarchive fallback in the wake prompt, the rename reason without "archived copy", and both docs updated, the scenario passed; its non-desktop arm names neither `unbind_pr` nor `unarchive_session`.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario self-shift-authorization` reports `self-shift-authorization scenario passed.`
    - M2.red: fail. It reported `self-shift-authorization: a desktop ready --wake with self-shift declared does not cover five steps: …`, carrying the declared signature `five steps`.
    - M2.green: pass. With the hint saying `take these five steps now`, the scenario passed.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 277 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenarios run the real `keel shift ready --wake` and `resume` with and without the desktop variables, and assert the order Remote Control off < `unbind_pr` < `create_scheduled_task`, the fallback and permission names, the absence of "archived copy", and `five steps` under `self-shift`.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `README.md`, `keel/config.yaml`, `scripts/validate_plugin.py`, and this change's directory.
      - Findings: none
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
    - Contract: keel-task-capsule/v1 sha256:18cd2d478cd56a39f0de53eade98ab8458c0a9b63e68cb9957faf69b8a64f8d5
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.131.0; with the 5.131.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. Both MODIFIED requirements replace their counterparts in `openspec/specs/keel-shift-change/spec.md` and `openspec/specs/keel-standing-authorization/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the two scenarios check the markers, the changelog, and both promoted specs; the full suite runs on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, both published specs, and the files 1.1 changed.
      - Findings: the dated comment above `self-shift` in `keel/config.yaml`'s `authorize:` list still says "four outgoing shift steps". Discard reason: it records the owner's 2026-10-13 decision as it was made; the coverage itself is stated by the comment block above it, which 1.1 updated to five steps.
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "so its archived copy can be told apart" — the desktop hint in `src/core/shift.js`, `docs/shift-change.md`, and "方便和归档的副本区分" in `docs/shift-change.zh-CN.md`. Updated by: 1.1
- I2: "the four steps `keel shift ready --wake` prints" and "take these four steps" — `src/core/shift.js`, `README.md`, the `keel/config.yaml` comment, both shift-change docs ("交班前的四步"), and the `self-shift-authorization` scenario docstring. Updated by: 1.1
- I3: "It covers exactly the four steps" and "rename the outgoing session with `set_session_title` so its archived copy can be told apart" — `openspec/specs/keel-standing-authorization/spec.md` and `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1
- I4: native memory `desktop-auto-archive-eats-self-shift` ("check ~/Library/Logs/Claude/main.log") describes the defect as open. Discard reason: native memory is outside the repository; this session updates it when the release lands.

## Expectation Coverage

- E1: A desktop self-shift that follows the printed steps leaves no bound PR for the app's auto-archive to archive the cleared session over (D1). Covered by: 1.1
- E2: A wake that finds its session archived anyway unarchives it and still delivers, and says so (D3). Covered by: 1.1
- E3: The release carries it. Covered by: 2.1
- E4: A gap longer than one auto-archive sweep is measured with the new recipe. Durable owner: https://github.com/TanglmChris/keel/issues/326
- E5: Turning Remote Control off can block for hours, which would stall an unattended shift at step 1. Durable owner: https://github.com/TanglmChris/keel/issues/324

## Change Evidence

- C1: pass. `npm test` on the 5.131.0 tree reports `validation --all passed: baseline plus 277 scenarios, 1 skipped: output-survives-the-pipe.`
