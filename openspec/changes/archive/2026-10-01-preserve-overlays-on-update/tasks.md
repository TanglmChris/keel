## 1. Restore overlays

- [x] 1.1 Restore updates and report every installed target
  - Covers:
    - keel-openspec-surface-overlay / OpenSpec update restores every installed target overlay
    - keel-openspec-surface-overlay / Doctor reports overlays for all repository-installed targets
    - D1
    - D2
    - D3
    - D4
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-restores-overlays` runs public CLI update and doctor in mixed temporary repositories; verifies exactly one overlay, retained upstream content, repeat updates, foreign-target missing diagnosis, both Codex layouts, absent-target isolation, and failed-update exit/no replay.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario openspec-surface-overlay` preserves existing install/refresh behavior.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a4d237066b48d42216893d2bb3c54317e35151dbdbed4248fb63e3323b8e47ec
    - M1: pass. Public CLI scenario update-restores-overlays passes against OpenSpec 1.13.2: missing foreign-target overlays, real repeat update, all four managed actions, upstream body retained, legacy layout diagnosis, absent-target isolation, exact failed-update status and unchanged files.
    - M1.red: fail. Before implementation the same scenario reported: update-restores-overlays: doctor hid missing Codex overlays while selecting Claude.
    - M1.green: pass. Same public CLI scenario passes after implementation.
    - M2: pass. Existing openspec-surface-overlay scenario passes, including install, refresh and all supported targets.
    - Review:
      - Status: pass
      - Acceptance check: real upstream updates exercise replacement and replay, while doctor checks expose missing .agents and legacy Codex coverage; failed update preserves upstream exit status and bytes.
      - Scope check: only bin/keel.js, scripts/validate_plugin.py and keel/CHANGELOG.md changed besides this change record.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Publish authority

- [x] 2.1 Sync requirements and document the repaired update
  - Covers:
    - D1
    - D2
  - Touch:
    - openspec/specs/keel-openspec-surface-overlay/spec.md
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: evidence-first
    - Reason: sync and user instructions publish behavior already proven by task 1.1.
    - M1: `keel openspec validate preserve-overlays-on-update --strict` validates the delta, and both READMEs state update restoration and all-target diagnostics matching the published requirements.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:7eee5a44e763ce09dcf67d2eba1791aa55cd393cb57a3d50c48a5ba788ea4a92
    - M1: pass. keel openspec validate preserve-overlays-on-update --strict reports valid; both README instructions match the published update-restoration and multi-target doctor requirements.
    - Review:
      - Status: pass
      - Acceptance check: the published spec matches the tested delta and both languages describe the working public command.
      - Scope check: only the published overlay spec and the two README files changed during this task.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 3. Repository delivery

- [x] 3.1 Commit the reviewed repair
  - Mode: repo-action
  - Covers:
    - D1
    - D2
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - Reason: repository delivery records reviewed content and does not add behavior.
    - M1: `git show --stat HEAD` identifies the repair commit; `git diff --exit-code` confirms committed product files.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f5a126da4b235c0afe97418f0364ce437b01379b6efd57336a37b2d72f4d6aab
    - M1: pass. git show --stat HEAD identifies 627d6ec, the reviewed overlay repair; git diff --exit-code passed before recording this delivery evidence.
    - Review:
      - Status: pass
      - Acceptance check: commit records both proven behavior and published authority.
      - Scope check: this repo-action wrote no product files; only record-layer evidence was updated after commit.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` in a clean source snapshot passes baseline and all registered scenarios.

## Change Evidence

- C1: pass. Clean snapshot of main b599ae6 plus the repaired CLI and registered scenario: npm test passed baseline plus 209 scenarios, 1 macOS F_SETPIPE_SZ skip. Snapshot Git metadata and temporary npm cache isolate old worktrees and personal cache; local fake Slack services ran with sandbox escalation. Log: /private/tmp/keel-issue-maintenance-full-test.log.

## Invalidates

- None.

## Expectation Coverage

- E1: Updates restore all installed target overlays without masking failure or creating absent surfaces. Covered by: 1.1, 2.1
- E2: Doctor reveals foreign-target missing overlays, respecting actual layouts. Covered by: 1.1, 2.1

## Archive Review — 2026-10-01

- Status: pass
- Acceptance check: Rechecked completed task evidence and public-interface verification; every delta requirement is present in the published specs. All 29 published specs pass strict validation.
- Scope check: This closure only synchronizes published specifications and moves the completed change with its metadata and evidence; no implementation or task contract is changed.
- Findings: none. Existing follow-up ownership remains as recorded in the task Reviews.
