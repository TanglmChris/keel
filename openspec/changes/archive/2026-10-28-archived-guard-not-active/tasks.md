# Tasks

## 1. An archived guard manifest holds nothing anywhere

- [x] 1.1 Decide whether a guard holds from `keel guard status`, in shift check, context, and adopt
  - Covers:
    - keel-shift-change / An archived guard manifest is not a task in progress / A manifest over an archived task does not block the hand-over
    - keel-shift-change / An archived guard manifest is not a task in progress / A manifest over a live task still blocks it
    - keel-stateless-continuity / Context names the refresh of an older managed protocol / An archived manifest does not defer the refresh
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/archived-guard-not-active/design.md
    - src/core/guard.js
    - src/core/shift.js
    - src/core/context.js
    - bin/keel.js
    - scripts/validation/shift.py
    - scripts/validation/hosts.py
  - Touch:
    - src/core/guard.js
    - src/core/shift.js
    - src/core/context.js
    - bin/keel.js
    - scripts/validation/common.py
    - scripts/validation/shift.py
    - scripts/validation/hosts.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-check-archived-guard-is-not-in-progress`: in a `shift_scratch` worktree that ignores `keel/guard.json` and is otherwise clean, a shape-valid manifest guarding `demo#1.1`, checked in `openspec/changes/archive/2026-10-28-demo/tasks.md`, leaves the real `keel shift check --json` exiting 0 with no `task-in-progress` item and a note containing `keel guard clear`; with `openspec/changes/demo/tasks.md` restored as a live change, it exits 1 with a `task-in-progress` item. Fails with: `shift-check-archived-guard-is-not-in-progress:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario context-archived-guard-does-not-defer-refresh`: an installed repository stamped 5.0.0 that authorizes `protocol-refresh` and holds the same archived manifest prints one `Protocol:` line from the real `keel context` containing `standing-authorized` and not `deferred`. Fails with: `context-archived-guard-does-not-defer-refresh:`
    - M3: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-adopts-idle-sessions`: an added idle session started before the update, whose `cwd` holds only the archived manifest, is stopped and resumed by the real `keel --update --adopt`, while `rtl · old guarded` (an `invalid` manifest) is still left alone. Fails with: `the session whose worktree holds only an archived manifest`
    - M4 (regression): run one at a time, each passes: `--scenario context-names-the-protocol-refresh`, `--scenario assertion-shape-count`, `--scenario surfaces-agree-with-code`, and `node scripts/run_python.js scripts/validate_plugin.py --group shift --jobs 4`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:275288b85cd124f2d719956cc8f0a1844effd3cc8cfe7a705a8c9f6c92ddb14d (keel 5.214.0)
    - M1: pass. `shift-check-archived-guard-is-not-in-progress scenario passed.` (exit 0).
    - M1.red: fail. With `src` and `bin` reverted to origin/main, exit 1: `shift-check-archived-guard-is-not-in-progress: an archived manifest is reported as task-in-progress: { "ready": false, … "kind": "task-in-progress", "detail": "keel/guard.jso…` — the fixture manifest read `Status: archived` from `keel guard status`, and the check still blocked on it.
    - M1.green: pass. `guardHolds` (`src/core/guard.js`) is false only for `absent` and `archived` (D1); `check` in `src/core/shift.js` reports an archived manifest as the note "keel/guard.json guards demo#1.1, which is checked and archived, so it enforces nothing; `keel guard clear` removes it" and no item (D2). The same manifest over a live `openspec/changes/demo` still gives a `task-in-progress` item and exit 1.
    - M2: pass. `context-archived-guard-does-not-defer-refresh scenario passed.` (exit 0).
    - M2.red: fail. With `src` and `bin` reverted to origin/main, exit 1: `context-archived-guard-does-not-defer-refresh: an archived manifest deferred the refresh: ["Protocol: AGENTS.md is stamped 5.0.0, older than Keel 5.214.0; refresh with `keel --install --target claude` — deferred while a task's write guard is active, …"]`.
    - M2.green: pass. `protocolRefresh` in `src/core/context.js` sets `deferred` from `guardHolds(repo)`; the line reads standing-authorized with the archived manifest present.
    - M3: pass. `update-adopts-idle-sessions scenario passed.` (exit 0).
    - M3.red: fail. With `src` and `bin` reverted to origin/main, exit 1: `update-adopts-idle-sessions: --adopt left alone the session whose worktree holds only an archived manifest: "… ip · old finished (ffffffff), under a task's write guard …"`.
    - M3.green: pass. The adopt loop in `bin/keel.js` asks `guardHolds(row.cwd)`; `ffffffff` is stopped and resumed with `--bg --resume ffffffff-…-000000000006`, and `rtl · old guarded` (an `invalid` `{}` manifest) is still left "under a task's write guard".
    - M4: pass. Run one at a time, each exit 0: `context-names-the-protocol-refresh scenario passed.` (its M3 `{}` manifest still defers the refresh), `assertion-shape-count scenario passed: 74 sites`, `surfaces-agree-with-code scenario passed.`, and `validation --group shift passed: 70 scenarios.`.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel shift check`, `keel context`, and `keel --update --adopt`, a manifest `keel guard status` reads as `archived` no longer blocks the hand-over (it is named as a note with `keel guard clear`), defers the protocol refresh, or keeps an idle session from being adopted (M1–M3); a manifest over a live change and an `invalid` manifest still do (M1, M3, M4).
      - Scope check: `git status --short` lists `bin/keel.js`, `src/core/context.js`, `src/core/guard.js`, `src/core/shift.js`, `scripts/validation/common.py`, `scripts/validation/hosts.py`, `scripts/validation/registry.py`, `scripts/validation/shift.py`, and this change's directory, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the specs
  - Covers:
    - E2
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-shift-change/spec.md
    - openspec/specs/keel-stateless-continuity/spec.md
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
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the deltas are promoted into `keel-shift-change` and `keel-stateless-continuity`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:cc7f0837ee06fa88b18385eaed1e9eaa7d8bdd3f0e1cf2ebef260e4816f48f19 (keel 5.214.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.214.0 → 5.215.0. With the section "An archived guard manifest blocks no hand-over, defers no refresh, and keeps no session from adoption" written into the stub, `version-alignment scenario passed.` (exit 0).
    - M2: the added requirement is appended to `openspec/specs/keel-shift-change/spec.md`, the modified requirement replaces "Context names the refresh of an older managed protocol" in `openspec/specs/keel-stateless-continuity/spec.md`, and `published-specs-validate-strictly scenario passed: 34 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test`: `validation --all passed: baseline plus 357 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: the release carries task 1.1's behavior, the markers agree at 5.215.0, the promoted specs validate strictly, and the full suite passes.
      - Scope check: `git status --short` lists the bumped markers, `keel/CHANGELOG.md`, the two published specs, task 1.1's files, and this change's directory, all in Touch of 1.1 or 2.1.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "keel/guard.json: a task's write guard is still active; complete the task or clear the guard" — `check` in `src/core/shift.js`, printed for a manifest that enforces nothing. Updated by: 1.1.
- I2: "`keel/guard.json` exists — the line says the refresh is deferred while a task's write guard is active" — the scenario "A write guard defers the refresh" in `openspec/specs/keel-stateless-continuity/spec.md`. Updated by: 2.1.
- I3: "one whose worktree has an active write guard (`keel/guard.json`, #204)" — `docs/updating.md`. Discard reason: still true; an archived manifest is not an active guard, and the sentence already says "active".

## Expectation Coverage

- E1: A manifest over a checked, archived task blocks no hand-over, defers no refresh, and keeps no session from being adopted, while every other manifest state still does (D1–D3) (#496). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
