# Tasks

## 1. A moved session is not a twin

- [x] 1.1 Count a role's live session only while its record does not name another role
  - Covers:
    - keel-cross-host-mailbox / Two live sessions on one role are reported / A session that bound another role is not a twin
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/twin-warning-own-role/design.md
    - src/core/chat/notice.js
    - scripts/validation/shift.py
  - Touch:
    - src/core/chat/notice.js
    - scripts/validation/shift.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario moved-session-is-not-a-twin`: in the `shift_scratch` fixture, live CLI sessions `sess-a` (this process) and `sess-b` (a running `sleep`) start in `verify`'s worktree through the real SessionStart hook, then `sess-b` runs the real `keel chat role --set fe` in a new worktree `fe` with its transcript under `CLAUDE_CONFIG_DIR`; `keel context --json` in `verify`'s worktree as `sess-a` carries no warning containing `live sessions` while `sess-b` still runs. Fails with: `moved-session-is-not-a-twin:`
    - M2 (regression): run one at a time, each passes: `--scenario two-live-sessions-on-one-role` (two real sessions on one role are still reported), `--scenario chat-role-park-and-unset`, and `--scenario assertion-shape-count`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8b46fa8161c3e556ad39af3f4afe0d741659abe3b54cfc6a7380c1de6b090faa (keel 5.211.0)
    - M1: pass. `moved-session-is-not-a-twin scenario passed.` (exit 0).
    - M1.red: fail. Before the change, exit 1: ``moved-session-is-not-a-twin: sess-b, now fe's, is still reported as a second verify session: ['2 live sessions are bound to role verify: sess-a (pid 12379, …/verify), sess-b (pid 12513, …/verify). They post under one name and share one read cursor, …']`` — the #490 warning. A first fixture placed sess-b's transcript in fe before SessionStart, so #415's visiting-session check never listed it under verify and the scenario passed with no fix; the fixture now starts both transcripts in verify, asserts the twin warning before the move, and gives sess-b a transcript in fe only when it enters it.
    - M1.green: pass. `twinWarning` counts a live entry only when `sessionStillRole` finds its `sessions/<id>.json` naming this role or finds no record (D1, D2). The session list is not edited (D3). With sess-b bound to fe and still running, `keel context` in verify carried no `live sessions` warning.
    - M2: pass. Run one at a time, each exit 0: `two-live-sessions-on-one-role scenario passed.` (two real sessions on one role are still reported), `chat-role-park-and-unset scenario passed.`, `assertion-shape-count scenario passed: 74 sites`.
    - Review:
      - Status: pass
      - Acceptance check: through the real SessionStart hook, the real `keel chat role --set fe`, and the real `keel context --json`, the twin warning that the fixture shows before sess-b moves is gone after it binds fe while it still runs (M1), and two sessions that both stay `verify`'s are still reported (M2).
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, and this change's directory, all in Touch.
      - Findings: Resolved here: M1 — the first fixture could not fail, which the scenario now guards with a before-move assertion; and `assertion-shape-count` caught a check in the new scenario guarding two failures with one message, split before M1 was rerun.
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
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-cross-host-mailbox/spec.md
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
    - M2: the delta is promoted into `keel-cross-host-mailbox`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8095ca46c601f70b86e6fff19ca878e260183d8b5fb2b4b280ee67bde9b6413a (keel 5.212.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.212.0 → 5.213.0. With the section "A session that bound another role is no twin of its first" written into the stub, `version-alignment scenario passed.` (exit 0).
    - M2: the modified requirement replaces its published form in `openspec/specs/keel-cross-host-mailbox/spec.md`, and `published-specs-validate-strictly scenario passed: 34 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test`, after `origin/main` (5.212.0) was merged in: `validation --all passed: baseline plus 353 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: the release carries task 1.1's behavior, the markers agree at 5.213.0, the promoted spec validates strictly, and the full suite passes.
      - Scope check: `git status --short` lists the bumped markers, `keel/CHANGELOG.md`, the published spec, and this change's directory, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "When two or more of a role's recorded sessions are live, `keel context` MUST warn" — the requirement "Two live sessions on one role are reported" in `openspec/specs/keel-cross-host-mailbox/spec.md`, which counts a session that has since bound another role. Updated by: 2.1.

## Expectation Coverage

- E1: A session that started under one role and bound another is not counted as a twin of the first, while a real second session still is (D1, D2); the session list itself is left to age out (D3) (#490). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
