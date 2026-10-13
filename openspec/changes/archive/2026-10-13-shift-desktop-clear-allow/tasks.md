# Tasks

## 1. Name the clear's allow entry

- [x] 1.1 The desktop partner step names `mcp__ccd_session_mgmt__clear_session` and why
  - Covers:
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A desktop self-shift is told how its next session gets started
    - D1
    - D2
    - F1
    - F2
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` passes with its desktop arm also requiring `mcp__ccd_session_mgmt__clear_session` and `refuses` in the `ready --wake` output, its non-desktop arm requiring neither, and both shift-change docs naming `mcp__ccd_session_mgmt__clear_session`. Fails with: `mcp__ccd_session_mgmt__clear_session`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1311f3d055d39328d6a2c7b7ca6157296ad357c0ba033029a0ebe9ece538e7c3
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-desktop-wake` reports `shift-desktop-wake scenario passed.`
    - M1.red: fail. With the scenario extended first, it reported `shift-desktop-wake: the desktop clear hint does not name mcp__ccd_session_mgmt__clear_session: …`, carrying the declared signature `mcp__ccd_session_mgmt__clear_session`.
    - M1.green: pass. With the partner step's last sentence naming both allow entries and the reason, and both docs updated, the scenario passed. Its non-desktop arm still names none of `send_message`, `create_scheduled_task` or `mcp__ccd_session_mgmt__clear_session`.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 275 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel shift ready --wake` with and without the desktop variables and reads its stdout and both docs; the reason (`refuses`) is asserted beside the entry name.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: none
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
    - M2: the MODIFIED requirement replaces its counterpart in `openspec/specs/keel-shift-change/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e816f447e963a83c5ea909aab60b4fe900ac6085f71a29b24f07f4797f5b694d
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.128.0; with the 5.128.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its counterpart in `openspec/specs/keel-shift-change/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the two scenarios check the markers, the changelog, and the promoted spec, and the full suite runs on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the published spec, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "Turning Remote Control back on unattended needs `mcp__ccd_session_mgmt__set_remote_control` in `permissions.allow`." — the desktop clear hint in `src/core/shift.js`, which names only one of the two entries an unattended run needs, and the matching sentences in both shift-change docs. Updated by: 1.1
- I2: "The output MUST also name the `permissions.allow` entry `mcp__ccd_session_mgmt__set_remote_control` that step needs." — `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: An owner following the desktop recipe learns, before the clear, that the clear must not wait for approval (D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.128.0 tree reports `validation --all passed: baseline plus 275 scenarios, 1 skipped: output-survives-the-pipe.`
