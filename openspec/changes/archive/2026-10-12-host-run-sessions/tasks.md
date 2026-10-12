# Tasks

## 1. Host runs

- [x] 1.1 A scheduled run is recognized by its first prompt and leaves the role alone, and the wake settles
  - Covers:
    - keel-cross-host-mailbox / A host-run session does not act as the worktree's role / A scheduled run leaves the role's presence alone
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A host run's start does not wake the role
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / The cleared session is woken once
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
    - F2
    - F3
    - F4
  - Read:
    - src/core/chat/notice.js
    - src/core/shift.js
  - Touch:
    - src/core/chat/notice.js
    - src/core/shift.js
    - src/core/patrol.js
    - docs/shift-change.md
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario host-run-session` with `KEEL_SHIFT_WAKE_POLL_MS=100` and `KEEL_SHIFT_WAKE_SETTLE_MS=1500` has `verify` run `keel shift ready --wake`, then feeds `keel chat hook` a `session-start` (source `startup`, session `run1`) and a `user-prompt-submit` for `run1` whose prompt starts with `<scheduled-task name="patrol">`, and requires: `verify`'s presence after the prompt equal to before the start, the prompt hook printing no chat notice, no `keel-shift` record 3 s later, and after a `session-end` for `run1` the presence still unchanged; then a `session-start` with source `clear` (session `s2`) and an ordinary prompt yield exactly one `keel-shift` record within 6 s; and `keel patrol task` names creating the task from a folder bound to no role. Fails with: `host-run-session:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario, `shift-self-wake` and `chat-claude-hooks` among them.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d834f8da3da4d77c5448b0b24c4d218a0d98c714f18dd3b5b3f77fc4d38264ff
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario host-run-session` reports `host-run-session scenario passed.`
    - M1.red: fail. Before the change the scenario reported `host-run-session: the host run's presence was not restored: …`, carrying the declared signature `host-run-session:` — the run's SessionStart had replaced `verify`'s presence, as `iecc-pm`'s was on 2026-10-12.
    - M1.green: pass. With the per-session file, the first-prompt decision, the host-run early return, and the settling waiter: after the `<scheduled-task name="patrol">` prompt `verify`'s presence equals what it was before `run1` started, the prompt hook prints nothing although `verify` had an unread mention, no `keel-shift` record exists 3 s later, `run1`'s SessionEnd leaves presence unchanged, the `clear` start of `s2` yields exactly one `keel-shift` record, and `keel patrol task` says to create the task from a folder bound to no role.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 267 scenarios, 1 skipped: output-survives-the-pipe.` `shift-self-wake` first failed (`found 0` within its 5 s) under the new 15 s default settle; its environment now sets `KEEL_SHIFT_WAKE_SETTLE_MS=500`, and it passes with its assertions unchanged.
    - Review:
      - Status: pass
      - Acceptance check: the scenario feeds the real `keel chat hook` host-shaped payloads with session ids and a prompt in the shape observed in the rtl_ppa_prj transcript, and reads the presence file, hook stdout, and the chat log, with the real detached waiter running.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `src/core/shift.js`, `src/core/patrol.js`, `docs/shift-change.md`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: the `<scheduled-task` marker is an observed Claude desktop format (2.1.295), not a contract; if it changes, recognition silently stops and runs act as the role again. The `keel patrol task` line telling the model to create the task from a folder bound to no role is the guard that does not depend on it.
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
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-cross-host-mailbox/spec.md
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
    - M2: the ADDED requirement is appended to `openspec/specs/keel-cross-host-mailbox/spec.md` and the MODIFIED requirement replaces its counterpart in `openspec/specs/keel-shift-change/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:72cb28d593fc00960a130d2dce631450e7bbaccc769dcf5ce84685c6079dc898
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.117.0; with the 5.117.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-cross-host-mailbox/spec.md` and the MODIFIED requirement replaces its counterpart in `openspec/specs/keel-shift-change/spec.md`; `published-specs-validate-strictly` reports `34 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the version markers, the changelog section, and both promoted specs are checked by the two scenarios, and the full suite passes on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the two published specs, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "Do not change into that directory: run every command with the paths given, so this session does not act as" — the `keel patrol task` prompt in `src/core/patrol.js`, which assumes the run starts elsewhere. Updated by: 1.1
- I2: "once the role's presence shows a session started with source `clear` or `startup` at or after the `ready`" — `openspec/specs/keel-shift-change/spec.md`, and "When the role's next session starts" in `docs/shift-change.md`. Updated by: 1.1, 2.1

## Expectation Coverage

- E1: A host scheduled run started in a role's worktree neither changes that role's presence nor triggers its wake, while an ordinary session still does (D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.117.0 tree reports `validation --all passed: baseline plus 267 scenarios, 1 skipped: output-survives-the-pipe.`
