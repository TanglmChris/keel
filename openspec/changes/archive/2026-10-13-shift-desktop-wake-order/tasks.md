# Tasks

## 1. Desktop recipe and restore

- [x] 1.1 The desktop recipe gives the four steps in order and the restore the woken session needs
  - Covers:
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A desktop self-shift is told how its next session gets started
    - keel-shift-change / The new shift resumes from the note / A resumed desktop shift is told to restore Remote Control
    - D1
    - D2
    - F1
    - F2
    - F4
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` follows the scenario through the real `keel shift ready --wake` and `keel shift resume`. With the desktop variables, the output names `create_scheduled_task`, `send_message`, `local_test-319`, `set_session_title`, `mcp__ccd_session_mgmt__set_remote_control` and `shift-restore`; `set_remote_control("self", false)` appears before `create_scheduled_task`; the output names neither `mcp__ccd_session_mgmt__clear_session` nor `The wake is armed`; and `resume` names `set_remote_control` and `set_session_title`. Without the variables, none of these desktop lines appear. Both shift-change docs name `set_session_title` and `shift-restore`. Fails with: `set_session_title`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5205ff1f005f88d01fe31b7014a301a51f532ceadfa525c5d0e364d50d85a745
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` reports `shift-desktop-wake scenario passed.`
    - M1.red: fail. With the scenario updated first, it reported `shift-desktop-wake: the desktop clear hint does not name set_session_title: …`, carrying the declared signature `set_session_title`.
    - M1.green: pass. With the four ordered steps in the desktop hint, the restore line in `resume`, and both docs rewritten, the scenario passed. Its non-desktop arm names none of `send_message`, `create_scheduled_task`, `set_session_title` or `shift-restore`.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel shift ready --wake` and `keel shift resume` with and without the desktop variables. It asserts that the `set_remote_control("self", false)` step comes before `create_scheduled_task`, that the wrong `clear_session` reason is gone, and that the rename and restore lines appear only on the desktop app.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, and this change's own directory. A full run at this point failed only `authored-scenario-names-are-registered`, on the scenario names task 1.2 declares and registers. The suite is therefore deferred to C1.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 `shift-restore` is a standing-authorization name, and `resume` reads it
  - Covers:
    - keel-standing-authorization / Restoring a session after a desktop shift is a named authorization / shift-restore is accepted and listed
    - keel-standing-authorization / Restoring a session after a desktop shift is a named authorization / A scoped shift-restore is refused
    - keel-shift-change / The new shift resumes from the note / A declared shift-restore lets the woken session restore without asking
    - D3
    - D4
    - D5
    - F3
  - Read:
    - src/core/config.js
  - Touch:
    - src/core/config.js
    - src/core/shift.js
    - keel/config.yaml
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-restore-authorization` passes. In a temporary repository, `authorize:` with `commit` and `shift-restore` is read and `keel --doctor` lists `shift-restore`; `shift-restore:anything` authorizes nothing and is named in the message. A desktop `keel shift resume` says `Standing-authorized by \`shift-restore\`` when it is declared, and names `shift-restore` as the declaration that would, without that sentence, when it is not. Fails with: `shift-restore-authorization:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization-declaration` and `--scenario continuation-docs`, which pin the vocabulary and the accepted-names text, pass, and `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:97a56f6f7f8be0c03882118d339552b9be1f5e8b510b00204f827804920b64a4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-restore-authorization` reports `shift-restore-authorization scenario passed.`
    - M1.red: fail. With the scenario written first and `shift-restore` absent from the vocabulary, it reported `shift-restore-authorization: shift-restore was not read as a standing authorization: …`, carrying the declared signature `shift-restore-authorization:`.
    - M1.green: pass. With `shift-restore` in `STANDING_AUTHORIZATION_ACTIONS`, the scenario's next run stopped at `a desktop resume with shift-restore declared does not say it is standing-authorized: No shift note waits for verify.`. The cause was the fixture: its uncommitted `keel/config.yaml` made `ready` refuse. The fixture's `ready` now passes `--force-reason`. With `resume` reading the declaration, the scenario passed: it says `Standing-authorized by \`shift-restore\`` only when declared, names `shift-restore` otherwise, and `shift-restore:anything` is refused by name.
    - M2: pass. `standing-authorization-declaration` and `continuation-docs` pass, and `npm test` reports `validation --all passed: baseline plus 276 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario reads the real `keel --doctor` and a desktop `keel shift resume` in a temporary repository, once with `shift-restore` declared, once without, and once with a scoped form.
      - Scope check: `git status --short` lists `src/core/config.js`, `src/core/shift.js`, `keel/config.yaml`, `README.md`, `scripts/validate_plugin.py`, and the 1.1 files. This repository's `authorize:` now declares `shift-restore` (D5).
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: both MODIFIED requirements replace their counterparts in `openspec/specs/keel-shift-change/spec.md`, the ADDED requirement is appended to `openspec/specs/keel-standing-authorization/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:977c9bc0ad20be2526e6442c460b439fa75f65629badf6723f4ac163c6a73f7c
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.129.0; with the 5.129.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. Both MODIFIED requirements replace their counterparts in `openspec/specs/keel-shift-change/spec.md`, and the ADDED requirement is appended to `openspec/specs/keel-standing-authorization/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the two scenarios check the markers, the changelog, and both promoted specs, and the full suite runs on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, both published specs, and the files 1.1 and 1.2 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "Unattended, this needs two `permissions.allow` entries: … `mcp__ccd_session_mgmt__clear_session`, because a clear left waiting for approval lets the wake arrive first and the app then refuses it." — the desktop hint in `src/core/shift.js`, and the matching sentences in `docs/shift-change.md` and `docs/shift-change.zh-CN.md`. That reason was wrong (F1). Updated by: 1.1
- I2: "Before you clear, create a one-shot scheduled task" — the same hint and docs, whose order lets the wake fire first (F1). Updated by: 1.1
- I3: "First turn Remote Control back on with set_remote_control(\"self\", true), then run `keel context` and `keel shift resume`." — the wake message text in the hint. Updated by: 1.1
- I4: The accepted-names vocabulary "… cleanup:scratch, push-protected:<branch glob>[@<role>]" — `README.md`, the `keel/config.yaml` comment, and `ACCEPTED_AUTHORIZE_NAMES` in `scripts/validate_plugin.py`. Updated by: 1.2
- I5: "names the `permissions.allow` entry … and the entry `mcp__ccd_session_mgmt__clear_session`" — `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1
- I6: "5.128.0 (PR #322) names it in the recipe" — native memory `remote-control-drops-on-self-shift`. Discard reason: native memory is outside the repository; this session corrected it on 2026-10-13 and will stamp 5.129.0 when it lands.

## Expectation Coverage

- E1: A desktop self-shift that follows the printed steps cannot have its clear refused by its own wake, and leaves a renamed outgoing session (D1, F4). Covered by: 1.1
- E2: A woken session in a repository that declared `shift-restore` restores Remote Control and its title without stopping to ask (D3–D5). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1
- E4: Why turning Remote Control off blocks in a session followed remotely. Durable owner: https://github.com/TanglmChris/keel/issues/319

## Change Evidence

- C1: pass. `npm test` on the 5.129.0 tree reports `validation --all passed: baseline plus 276 scenarios, 1 skipped: output-survives-the-pipe.`
