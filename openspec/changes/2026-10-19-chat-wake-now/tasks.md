# Tasks

## 1. A role's ended CLI session is resumed in one step

- [x] 1.1 Record CLI sessions; add `keel chat wake now`; let `keel tick` resume exited roles
  - Covers:
    - keel-cross-host-mailbox / Presence is visible and only an owner-installed waker launches a member / An ended CLI session is resumed in one step
    - D1
    - D2
    - D3
    - D4
    - D5
  - Read:
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - src/core/tick.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - src/core/tick.js
    - src/core/patrol.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-now-cli` runs the real chat hooks as a CLI session `sess-verify-1` with an exited `CLAUDE_PID`, and the real `keel chat` and `keel tick` with `KEEL_CLAUDE` pointing at a fake that logs its arguments and working directory: a dm names `keel chat wake now verify` and not `get_session`; `keel chat wake now verify` runs the fake once with exactly `--bg --resume sess-verify-1 <prompt naming keel chat unread>` in verify's worktree; with a running pid it runs nothing and says `running`; `keel tick` resumes the exited role once for a new dm, not again on the next tick, and not for a dm to it while parked; a `keel patrol --nudge` escalation for it names `keel chat wake now verify` and not `get_session`. Fails with: `does not name `
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:038ab89a41575c810d179e071ddffa29871db72442dadd0463625c7211fc2c3c (keel 5.152.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-now-cli` reports `chat-wake-now-cli scenario passed.`
    - M1.red: fail. With the scenario written first and the code unchanged: `chat-wake-now-cli: a dm to a role whose CLI process exited does not name `keel chat wake now verify`: 'Posted … to dm-rtl--verify.\n'`, carrying the declared signature. After the reauthorization, with the patrol case added and `patrol.js` unchanged: `the patrol's nudge escalation for an ended CLI session is not `keel chat wake now verify`: … verify's desktop session sess-verify-1 … get_session …`.
    - M1.green: pass. With presence recording `cli_session`/`cli_pid`/`cli_worktree`, `asleep` reporting an exited CLI process, `resumeCli` running exactly `claude --bg --resume <id> <prompt>` in the recorded worktree, `keel chat wake now`, `keel tick` resuming once per new record for unparked roles, and the post and patrol messages naming `keel chat wake now <role>`, the scenario passed.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 299 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit. The run before it failed `update-host-query-timeout` once under parallel load and passed alone; its limits are widened in this task, see Findings.
    - Review:
      - Status: pass
      - Acceptance check: through the real hooks, `keel chat` and `keel tick`, with a fake `claude` that records its arguments and directory: a dm to the exited CLI role names `keel chat wake now verify`; the command resumes `sess-verify-1` with only `--bg --resume <id> <prompt>` in verify's worktree; a running pid resumes nothing; the tick resumes once per new record and never while the role is parked; the patrol escalation names the one-step wake.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `src/core/chat/cli.js`, `src/core/tick.js`, `src/core/patrol.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: the real `claude --bg --resume` was exercised by hand on 2026-10-19 (memory: CLI background session wake facts) rather than in the suite, which has no `claude` on CI; the suite pins the exact argument list that measurement showed keeps the session id.
        - Resolved here: M2 — `update-host-query-timeout` (#365) flaked under parallel load because every case ran with a 1.5 s query limit; the exit-3 and missing-host cases now keep 30 s and only the hung and dry-run cases use 4 s against a 15 s hold, and the full suite passes with it.
    - Blocker: none
    - Reauthorizations: 2026-10-19 — before any Evidence: `patrol.js`'s nudge escalation also calls `asleep`, and would have given a CLI role the desktop step; `src/core/patrol.js` added to Touch and M1 extended to it; anchor re-recorded.

## 2. Release

- [ ] 2.1 Release and promote the spec
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta requirements are promoted into `keel-cross-host-mailbox`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract:
    - M1:
    - M2:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Keel MUST NOT start any session except through a waker the owner installed for that role on that machine with `keel chat wake add`" — `openspec/specs/keel-cross-host-mailbox/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: A role whose CLI session has ended is resumed by one command, or by the owner's waker, with its own session id (#348; D1, D2, D3, D4, D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
