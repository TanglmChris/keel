# Tasks

## 1. Follow the transcript that exists

- [x] 1.1 Resolve a resumed -w session's worktree from its existing transcript
  - Covers:
    - keel-cross-host-mailbox / A role records its own session and wakes only one that still exists / A resumed -w session whose reported transcript does not exist is recorded for its worktree
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/resume-transcript/design.md
    - src/core/chat/notice.js
  - Touch:
    - src/core/chat/notice.js
    - scripts/validation/chat.py
    - docs/host-contract.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-hook-follows-session-worktree`. A SessionStart payload in the measured resume shape is replayed: `source: resume`, `cwd` set to rtl's worktree, and a `transcript_path` in rtl's project directory that does not exist, with the real `<id>.jsonl` in verify's project directory under a scratch `CLAUDE_CONFIG_DIR`. The session is recorded as verify's, watches verify's signal and not rtl's, and leaves rtl's presence unchanged. The existing case still passes. Fails with: `chat-hook-follows-session-worktree:`
    - M2 (regression): these all pass: `--scenario chat-visitor-not-recorded`, `--scenario chat-role-set-records-session`, `--scenario chat-claude-hooks`, `--scenario chat-wake-now-cli`, `--scenario assertion-shape-count`, `--group chat`, and the baseline. Every scenario that `docs/host-contract.md` cites is registered.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:163dab0d2b35dea9dab490fefd3fbe3cdee4c5f0d0789bbec550fb18cdef58ee (keel 5.189.0)
    - M1: pass. `chat-hook-follows-session-worktree scenario passed.` The new case replays the measured resume payload: `source: resume`, `cwd` = rtl's worktree, and `transcript_path` in rtl's project directory where no file exists, with the real `sess-w.jsonl` in verify's project directory under a scratch `CLAUDE_CONFIG_DIR`. Results:
      - The session is recorded as verify's.
      - It watches verify's signal and not rtl's.
      - rtl's presence keeps `sess-r`.
      - verify's segment names the transcript that exists.
      - The #415 case still passes.
    - M1.red: `chat-hook-follows-session-worktree: a resumed -w session whose reported transcript does not exist watches ['…/rtl/.git/keel-chat/signal/rtl', '…/signal/worktree/a3c6645f6e5ebee8'], not verify's signal.` This was 5.189.0's `hookLocation`, and it matches what keel-maint-2's real resume printed: `signal/codex-issues` plus the main checkout's worktree signal.
    - M1.green: `chat-hook-follows-session-worktree scenario passed.` `existingTranscript()` returns the payload's `transcript_path` when that file exists. Otherwise it returns `<config>/projects/*/<session_id>.jsonl`. Both `hookLocation` and `recordSegment` use it.
    - M2: pass.
      - The baseline exits 0.
      - `--group chat` reports `validation --group chat passed: 47 scenarios.` This covers `chat-visitor-not-recorded`, `chat-role-set-records-session` and `chat-claude-hooks`.
      - `chat-wake-now-cli`, `assertion-shape-count` (74) and `release-evidence-classes` pass.
      - All 10 scenarios that `docs/host-contract.md` cites are registered.
    - Review:
      - Status: pass
      - Acceptance check: M1 feeds `keel chat hook session-start` the payload shape the host actually sent on 2026-10-21. The probe recorded it in #441. M1 then asserts the binding, the watch list, the segment, and that the other role is untouched, all through the hook's public entry point.
      - Scope check: the changes are in `src/core/chat/notice.js`, `scripts/validation/chat.py`, `docs/host-contract.md`, and this change's record.
      - Findings:
        - `recordSegment` also took the payload's `transcript_path`, so a resumed `-w` session's shift history pointed at a missing file. It now uses the transcript that exists, and M1 asserts the segment. Resolved here: M1
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
    - Contract:
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

- I1: In `docs/host-contract.md`, the row "Resumed after being started with `claude --bg -w`" says "SessionStart reports the directory it was launched from as `cwd`". The row says nothing about `transcript_path`. Updated by: 1.1.
- I2: In the 5.181.0 changelog, "The chat hook follows the session's real worktree". Discard reason: a changelog entry records what that release did, and this release's entry states the correction.

## Expectation Coverage

- E1: A resumed `claude --bg -w` session is bound to the worktree it runs in, even though the host reports the launch directory for both `cwd` and `transcript_path` (#441; D1–D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
