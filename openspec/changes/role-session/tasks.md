# Tasks

## 1. Record a role's own session

- [x] 1.1 Resolve the session's worktree, ignore visitors, record on `role --set`, and skip removed sessions
  - Covers:
    - keel-cross-host-mailbox / A role records its own session and wakes only one that still exists / A resumed session is recorded for the worktree it runs in
    - keel-cross-host-mailbox / A role records its own session and wakes only one that still exists / A visiting session does not become the role's session
    - keel-cross-host-mailbox / A role records its own session and wakes only one that still exists / Binding a role records the session that bound it
    - keel-cross-host-mailbox / A role records its own session and wakes only one that still exists / A removed session is not resumed
    - D1
    - D2
    - D3
    - D4
    - D5
  - Read:
    - openspec/changes/role-session/design.md
    - src/core/chat/notice.js
    - src/core/chat/cli.js
  - Touch:
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-hook-follows-session-worktree`: a SessionStart hook with `source: resume`, `cwd` rtl's worktree, and a `transcript_path` in the host project directory of verify's worktree records the session as verify's (presence `cli_session` and `cli_worktree`, session record `role: verify`), returns verify's signal among its watch paths and not rtl's, and leaves rtl's presence and session list unchanged. Fails with: `chat-hook-follows-session-worktree:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-visitor-not-recorded`: after rtl's session starts as rtl and verify's as verify, rtl's session running `keel chat unread` in verify's worktree, and a plain `keel chat unread` there with no Claude session, leave verify's `cli_session`, `cli_worktree`, and session list as verify's own. Fails with: `chat-visitor-not-recorded:`
    - M3: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-set-records-session`: a CLI session started in an unbound worktree that runs `keel chat role --set verify2` there is then verify2's presence `cli_session` with that worktree, its session record names verify2, and verify2's newest segment is its transcript. Fails with: `chat-role-set-records-session:`
    - M4: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-skips-removed-session`: with verify's recorded CLI process exited and a claude whose `agents --json --all` lists other sessions only, `keel chat wake now verify` runs no `--bg --resume`, exits nonzero, and says the session was removed. Fails with: `chat-wake-skips-removed-session:`
    - M5 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-now-cli`, `--scenario chat-claude-hooks`, `--scenario shift-cli-self-shift`, `--scenario shift-cli-keeps-old-sessions`, and the baseline pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6f8705f391aef08604c1355e3126851a5e9d38f86c822848051c61ccf5d6e427 (keel 5.180.0)
    - M1: pass. `chat-hook-follows-session-worktree scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `chat-hook-follows-session-worktree: a session whose transcript is verify's watches ['…/keel-chat/signal/rtl', …], not verify's signal alone.` (exit 1).
    - M1.green: pass. The hook now resolves its location with `hookLocation`: when the transcript's host project directory names another worktree of the repository (`git worktree list`), the hook uses that worktree.
    - M2: pass. `chat-visitor-not-recorded scenario passed.` (exit 0). The scenario includes a visiting session's `role --set verify` from inside verify's worktree, which leaves verify's record as it was.
    - M2.red: fail. Before the change: `chat-visitor-not-recorded: a visiting or session-less keel command replaced verify's recorded session: {'state': 'online', … 'session_source': 'startup', 'desktop_session': None, …` (exit 1).
    - M2.green: pass. Commands now call `commandPresence`, which records the session in full only when its record names the role, and otherwise touches only `state` and `last_active`. `recordBinding` requires the session's transcript to be in this worktree's project directory. The suite's `chat_environment` also strips `CLAUDE_CODE_SESSION_ID` and `CLAUDE_PID`. Before that, the suite inherited the running session's id, and the fixture's own `role --set` recorded it, unlike CI.
    - M3: pass. `chat-role-set-records-session scenario passed.` (exit 0).
    - M3.red: fail. Before the change: `chat-role-set-records-session: binding a role did not record the session that bound it: {}` (exit 1).
    - M3.green: pass. `role --set` now calls `recordBinding`, which writes the session record (decided, not a host run), touches presence in full with source `role-set`, and starts the role's segment with the transcript.
    - M4: pass. `chat-wake-skips-removed-session scenario passed.` (exit 0).
    - M4.red: fail. Before the change: `chat-wake-skips-removed-session: wake now resumed a session claude agents no longer lists: [['--bg', '--resume', 'sess-verify-1', …]]` (exit 1).
    - M4.green: pass. `resumeCli` now reads `claude agents --json --all` first. When the list parses and lacks the id, it returns `removed`, and `wake now` fails naming it. An unreadable list resumes as before.
    - M5: pass. These scenarios pass, and the baseline exits 0:
      - `chat-wake-now-cli`, whose call count now counts only `--bg` calls, since a wake first reads the agent list;
      - `chat-claude-hooks`, `shift-cli-self-shift`, `shift-cli-keeps-old-sessions`;
      - `assertion-shape-count`, at 74 after splitting two conditions in the new scenarios;
      - all 71 `chat-*`, `shift-*`, `mailbox-*`, `tick-*`, and `patrol-*` scenarios.
    - Review:
      - Status: pass
      - Acceptance check: E1 is met. Through the real `keel chat hook` and `keel chat` commands:
        - a `-w` session's resume is recorded for its own worktree;
        - a visitor's command or binding leaves the role's record alone;
        - the binding session is recorded;
        - a removed session is not resumed.

        The host behaviour behind D1 was measured on this repository (F1, F2).
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `src/core/chat/cli.js`, `scripts/validate_plugin.py`, and this change's directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

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
    - M2: the delta is promoted into `keel-cross-host-mailbox`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d93a316f5e966028dac5bd0cd1e7e3e26bfb4c8e33a86cc64a0bbe05e4fc0c4b (keel 5.180.0)
    - M1:
    - M2:
    - M3:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`keel chat role --set kaiwu-lead` printed `Chat role: kaiwu-lead`, but nothing it records changed" — the behavior #415 reports, in `src/core/chat/cli.js`. Updated by: 1.1.
- I2: "keel-maint-2 has recorded no Claude Code CLI session, so there is nothing to resume" for a role bound after its session started — `src/core/chat/cli.js`. Updated by: 1.1.

## Expectation Coverage

- E1: A role's recorded session is its own, follows `role --set`, survives a `-w` session's resume, and is never resumed once removed (#415; D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
