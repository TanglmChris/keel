# Tasks

## 1. Wake step for idle desktop sessions

- [x] 1.1 Presence records the desktop session; posts and patrol nudges name its wake step
  - Covers:
    - keel-cross-host-mailbox / Presence is visible and only an owner-installed waker launches a member / A todo for an idle desktop session names its wake step
    - keel-coordinator-patrol / The patrol nudges idle roles directly / A nudge to an idle desktop session is a risk at once
    - D1
    - D2
    - D3
    - D4
  - Read:
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - src/core/patrol.js
    - src/core/shift.js
  - Touch:
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - src/core/patrol.js
    - scripts/validate_plugin.py
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-idle-desktop` runs the real `keel chat hook session-start` for `verify` under `CLAUDE_CODE_ENTRYPOINT=claude-desktop`, `CLAUDE_CODE_HOST_SESSION_ID=local_test-331` and `KEEL_SHIFT_DESKTOP_PID` set to a process that has exited, then asserts the real `keel chat todo soc --assignee verify` from `rtl` stores the todo and names `send_message`, `get_session`, `unarchive_session` and `local_test-331`, with `asleep` in `--json`; that `keel patrol --nudge --idle 1s` nudges `verify` and prints a `risk:` line naming `local_test-331` and `send_message` on that first run; and that after `verify`'s session-start hook runs again outside the desktop app, a new todo names none of them. Fails with: `does not name send_message`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-nudge` still passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e75d4f496968198276ab6cf773c937c11880ae00c131fdfa658d383b7a8c9560
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-idle-desktop` reports `chat-wake-idle-desktop scenario passed.`
    - M1.red: fail. With the scenario written first, it reported `chat-wake-idle-desktop: a todo for an idle desktop session does not name send_message: Posted 20261014T153859803Z-rtl-9557ed to soc.`, carrying the declared signature `does not name send_message`.
    - M1.green: pass. With presence recording `desktop_session`/`desktop_pid`, `notice.asleep` checking the pid, `postResult` printing the wake step and `asleep` in `--json`, and `nudgeRoles` adding the risk, the scenario passed. Live on this session (2026-10-14 23:40): `presence/keel-maint.json` recorded `desktop_session: local_a4222dad-…`, the id `get_session("self")` reports, and `desktop_pid: 85901`, which `ps` shows is this session's running `claude` process.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-nudge` reports `patrol-nudge scenario passed.`
    - M3: pass. `npm test`: `validation --all passed: baseline plus 282 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real session-start hook under the desktop environment with a process that has exited, the real `chat todo` (text and `--json`), the real `patrol --nudge`, and a plain hook afterwards; each assertion reads command output, and the todo is read back through `chat todos --mine`.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `src/core/chat/cli.js`, `src/core/patrol.js`, `scripts/validate_plugin.py`, both chat docs, and this change's directory.
      - Findings: Keel prints the step and does not perform it; letting the posting session send `send_message` unasked would need a new `authorize:` scope, which is the owner's vocabulary call. Discard reason: #331's Expected accepts printing the step, and without a measured case of a printed step being skipped there is nothing to justify widening `authorize:`.
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
    - openspec/specs/keel-coordinator-patrol/spec.md
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
    - M2: both MODIFIED requirements replace their counterparts in the published specs, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d33d80b94d91eca59676ccde67ac37f7f137393db280d8d13d90fd2976110803
    - M1: `node scripts/bump_version.js minor` moved every marker 5.136.1 → 5.137.0; with the "Chat names the wake step for an idle desktop session" section written, `version-alignment scenario passed.` (exit 0).
    - M2: both MODIFIED requirements replaced their published counterparts, each adding its desktop scenario; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and both published specs carry the change; both validator scenarios pass.
      - Scope check: changed files are the version markers, `keel/CHANGELOG.md` and the two published specs, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Claude Code is woken by a file watcher that costs nothing until a message addressed to the session arrives" with no desktop-app exception — `docs/chat-slack-setup.md` and its zh-CN counterpart. Updated by: 1.1
- I2: "Posting a mention of an offline member MUST store the record and report the member as offline" as the only post-time report, and "The patrol nudges idle roles directly" with no desktop case — `openspec/specs/keel-cross-host-mailbox/spec.md`, `openspec/specs/keel-coordinator-patrol/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: On the desktop app, a todo, post, or patrol nudge to a role whose session has no running process says it wakes nothing there and names the step that does, and the patrol tells the coordinator on the first nudge (#331, D3, D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
