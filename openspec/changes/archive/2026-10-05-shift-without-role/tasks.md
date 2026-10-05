# Tasks

## 1. Shift change without a chat role

- [x] 1.1 `check`, `ready`, and `resume` work without a role, and `keel context` announces a waiting note
  - Covers:
    - keel-shift-change / The outgoing shift leaves a note and closes the request / A worktree without a chat role changes shift
    - keel-shift-change / The new shift resumes from the note / The notice points to the note and resume consumes it
    - D1
    - D2
    - D3
    - F1
    - F2
    - F3
  - Read:
    - src/core/shift.js
    - src/core/context.js
    - plugins/keel/scripts/session-start.js
  - Touch:
    - src/core/shift.js
    - src/core/context.js
    - plugins/keel/scripts/session-start.js
    - src/core/chat/notice.js
    - scripts/validate_plugin.py
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-without-role` runs, in a repository whose worktree has no chat role, `keel shift ready "next: rerun R007"` and requires exit 0 with the note under `keel-chat/shift/worktree/`; requires `keel context` and the SessionStart projection (`plugins/keel/scripts/session-start.js`) to name `keel shift resume` and `keel context --json` to keep the same `status` as before the note; requires `keel shift resume` to print the note and move it under `shift/history/`; and requires `keel context` afterwards not to name it, and both shift guides to say a chat role is optional. Fails with: `shift-without-role:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-change` requires the waiting-note line from the SessionStart projection instead of the chat hook, and still passes. Fails with: `shift-change:`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1e698d6e31cb338851ded2149630aec503ddb71c26609e9ff363d13820f8a102
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-without-role` reports `shift-without-role scenario passed.`
    - M1.red: fail. Before the change the scenario reported `shift-without-role: keel shift ready refused in a worktree without a chat role: keel shift: This worktree has no chat role, so the record would have no sender. …`, carrying the declared signature `shift-without-role:`.
    - M1.green: pass. With the note keyed per worktree when there is no role, `ready` and `resume` no longer requiring one, `keel context` carrying `shift` and a `Shift:` line, the SessionStart projection repeating it (also in a repository without `openspec/`, checked on disk before spawning anything), and both guides updated, the scenario passes. A manual run piped through `head` showed the check listing the pipe's own `head`. The check now skips its own process group, and the scenario's `sleep` runs in its own session, as a job a session leaves behind would.
    - M2: pass. `shift-change` reports `shift-change scenario passed.`
    - M2.red: fail. With the notice read from the SessionStart projection, before the change the scenario reported `shift-change: the session-start notice does not point to the waiting note.`, carrying the declared signature `shift-change:`.
    - M2.green: pass. With the projection line in place and the chat hook's duplicate removed, the scenario passes.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenarios read `keel context` text and JSON, the real SessionStart projection, the note files on disk, and resume's output, with and without a chat role. The status-unchanged assertion holds D3's promise not to move continuity.
      - Scope check: `git status --short` lists the seven Touch paths and this change's own directory.
      - Findings: none
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
    - M1: `node scripts/bump_version.js minor` moves every marker to 5.99.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.99.0 section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:282323411bb03dfdff39b81c3070105b97c6adc2d4ced15fc795f4f555cf13a6
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.99.0. With the 5.99.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The two MODIFIED requirements replace their published copies, keeping their scenarios and adding one; `published-specs-validate-strictly` reports `31 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published spec carries the role-optional clauses and the new scenario, and the changelog names the worktree note, the context line, and the process-group fix.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump reports `validation --all passed: baseline plus 239 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "Every session taking part in a shift change needs a chat role" as told to rtl_ppa_flow on 2026-10-05, and the 5.98.0 guides' framing of every step as a chat record — `docs/shift-change.md`, `docs/shift-change.zh-CN.md`. Updated by: 1.1

## Expectation Coverage

- E1: A shift change works where no chat role or bot is set up (D1, D2, D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
