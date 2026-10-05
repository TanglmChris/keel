# Tasks

## 1. Late role binding

- [x] 1.1 A session started before its role was bound still wakes
  - Covers:
    - keel-cross-host-mailbox / Only a mention wakes a session, and the notice is host-neutral / A worktree without a role is untouched
    - keel-cross-host-mailbox / Only a mention wakes a session, and the notice is host-neutral / A role bound after the session started still wakes it
    - keel-cross-host-mailbox / Only a mention wakes a session, and the notice is host-neutral / A mention wakes
    - D1
    - D2
    - D3
    - F1
    - F2
    - F3
    - F4
  - Read:
    - src/core/chat/notice.js
    - src/core/chat/store.js
  - Touch:
    - src/core/chat/notice.js
    - src/core/chat/store.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-claude-hooks` requires, in a repository worktree with no role, SessionStart to print only `watchPaths` naming one path under `signal/worktree/` and every other hook to print nothing, and outside a repository every hook to print nothing; then binds the role `late` in that worktree after SessionStart ran, has `rtl` post `@late please look`, and requires the path SessionStart named to have grown and the FileChanged hook there to exit 2. Fails with: `chat-claude-hooks:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-core`, `chat-records`, and `chat-wake-run` each pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f2345372f16d00f75d5c8e0cc815c5bdf41bbe9d6cb24d6c4c3c3f35c97c15da
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-claude-hooks` reports `chat-claude-hooks scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-claude-hooks: session-start in a worktree with no role does not watch exactly one worktree signal: ''`, carrying the declared signature `chat-claude-hooks:`.
    - M1.green: pass. With SessionStart returning `signal/worktree/<id>` for every repository worktree (alone when no role is bound, after the role's signal when one is) and `writeRecord` appending to the signal of each worktree bound to a woken role, the same scenario passes: a role bound after SessionStart grows the watched path and its FileChanged hook exits 2. The existing check of a bound session's `watchPaths` now expects the role's signal followed by the worktree signal.
    - M2: pass. `chat-core`, `chat-records`, and `chat-wake-run` each report `scenario passed.`
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real plugin hook script for SessionStart before the role exists, binds it afterwards through the CLI, posts a mention through the CLI, and observes the watched file and the FileChanged exit code, which is exactly the path the spec session failed on.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `src/core/chat/store.js`, and `scripts/validate_plugin.py`, all in Touch, plus this change's own directory. `assertion-shape-count` stays at 80 after splitting the conditions this task added.
      - Findings: none

## 2. Release

- [ ] 2.1 Release and promote the spec
  - Covers:
    - E1
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
    - M1: `node scripts/bump_version.js patch` moves every marker to 5.94.1, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.94.1 section written.
    - M2: the MODIFIED requirement replaces its published text in `openspec/specs/keel-cross-host-mailbox/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: pending
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pending

## Invalidates

- I1: "SessionStart also returns the role's signal path in `watchPaths`" and "With no role bound, every hook MUST exit 0 with no output" — `openspec/specs/keel-cross-host-mailbox/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: A session started before its worktree's role was bound wakes on the next record addressed to that role, with no plugin reload. Covered by: 1.1, 2.1
