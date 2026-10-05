# Tasks

## 1. Shift change

- [x] 1.1 `keel shift` runs a coordinated shift change from request to resume
  - Covers:
    - keel-shift-change / A coordinator requests a shift change and the role is woken / A request wakes the role
    - keel-shift-change / The readiness check reports what would be lost or left running / Each kind of loose end is reported
    - keel-shift-change / The readiness check reports what would be lost or left running / A clean worktree is ready
    - keel-shift-change / The outgoing shift leaves a note and closes the request / Ready is refused while loose ends remain
    - keel-shift-change / The outgoing shift leaves a note and closes the request / Ready stores the note and closes the request
    - keel-shift-change / The coordinator starts the new shift once its note waits / Start before ready is refused
    - keel-shift-change / The coordinator starts the new shift once its note waits / Start wakes the role with the resume instruction
    - keel-shift-change / The new shift resumes from the note / The notice points to the note and resume consumes it
    - keel-shift-change / Shift state is visible / Status follows the steps
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - D7
    - F2
    - F3
    - F4
  - Read:
    - src/core/chat/store.js
    - src/core/chat/notice.js
    - bin/keel.js
  - Touch:
    - src/core/shift.js
    - bin/keel.js
    - src/core/chat/notice.js
    - scripts/validate_plugin.py
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-change` drives the whole procedure in a scratch repository with a bare remote and the `rtl` and `verify` worktrees: `keel shift request verify` from `rtl` leaves an open `keel-shift` request in `dm-rtl--verify` and touches `verify`'s signal; `keel shift check` in `verify` exits 1 naming an uncommitted file, a commit not on the remote, `keel/guard.json`, a `sleep` started in the worktree by its PID, a linked worktree under the temporary directory, and an open chat `todo` assigned to `verify`, and exits 0 once each is cleared; `keel shift ready` is refused with items present and stores nothing, then stores the note at `keel-chat/shift/verify.md`, closes the request, and names `clear_session` and `/clear`; `keel shift start verify` is refused before ready and afterwards posts a message naming `keel shift resume` that touches the signal; `keel shift status` lists `verify` with a waiting note; the SessionStart hook names `keel shift resume` while the note waits; `keel shift resume` prints the note, moves it under `shift/history/`, posts an on-shift message, and the next notice no longer names it; and both guides exist and the READMEs link them. Fails with: `shift-change:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-claude-hooks`, `chat-records`, and `chat-owner-mention` each pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:134301bce98798bb70035e0420350c1e69e817c19b01f3ac3eae1a8d5d4b164e
    - Blocker: none
    - Reauthorizations: 2026-10-05 re-recorded after D4 was reworded to skip bare interactive shells, found when the check ran in this worktree. No evidence had been recorded yet.
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-change` reports `shift-change scenario passed.`
    - M1.red: fail. Before the change the scenario reported `shift-change: keel shift request failed: keel: repo path was provided more than once`, carrying the declared signature `shift-change:`.
    - M1.green: pass. With `src/core/shift.js` (request, check, ready, start, resume, status), the `keel shift` dispatch and help line in `bin/keel.js`, the waiting-note line in the SessionStart notice, both guides, and the README links, the same scenario passes. A run in this worktree first listed two terminal-tab `zsh -l` shells as live processes. Bare interactive shells are now skipped (D4 reworded, reauthorized below), and only what they run is listed.
    - M2: pass. `chat-claude-hooks`, `chat-records`, and `chat-owner-mention` each report `scenario passed.`
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives every step through the CLI, as the coordinator and the role would, against a real bare remote, a real `sleep`, a real temporary worktree, and the real SessionStart hook. Each refusal is checked along with what it must not do: no note stored, nothing posted.
      - Scope check: `git status --short` lists the eight Touch paths and this change's own directory.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/241 — a role's own `keel context` still reports other worktrees' changes; the shift note does not change that.
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
    - M1: `node scripts/bump_version.js minor` moves every marker to 5.98.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.98.0 section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2ecb8a80176d133d398391caa1464b96c5fdb7179168afe2053f484878ef6e0f
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.98.0. With the 5.98.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirements are promoted into a new `openspec/specs/keel-shift-change/spec.md`; `published-specs-validate-strictly` reports `31 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the new published spec carries the six requirements with their scenarios, and the changelog names each subcommand, where the note lives, and the guides.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the new spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump reports `validation --all passed: baseline plus 238 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: A role's session changes shift through Keel: requested, checked, noted, cleared, started, and resumed from the note (D1, D3, D4, D6). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
