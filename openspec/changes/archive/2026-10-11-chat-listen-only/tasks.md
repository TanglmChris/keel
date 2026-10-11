# Tasks

## 1. Listen-only members

- [x] 1.1 `group add --listen` makes a member that hears, acknowledges, and closes its todos but cannot post or change the group
  - Covers:
    - keel-cross-host-mailbox / A group member can be listen-only / A listen-only member hears and is refused a post
    - keel-cross-host-mailbox / A group member can be listen-only / A listen-only member may acknowledge and close its todo
    - keel-cross-host-mailbox / A group member can be listen-only / A listen-only member cannot change the group
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
    - F3
  - Read:
    - src/core/chat/store.js
    - src/core/chat/cli.js
  - Touch:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-listen-only` adds `review` to `soc` with `--listen` through the real CLI and requires: `rtl`'s mention of `review` in `review`'s `unread --json` and `notice --check` exiting 0; `post`, `todo`, `group add`, and `group archive` by `review` each exiting non-zero with `listen-only` in stderr; `ack` of an `--ack` record and `done` of an assigned todo by `review` exiting 0; and `group list` printing `review (listen)`. Fails with: `chat-listen-only:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:fa82f5a8337dbe3dba81c403bfa4882a7df9673df3743dbb46284b2a5b5e4ad0
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-listen-only` reports `chat-listen-only scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-listen-only: group add --listen failed: keel chat: Unknown option for keel chat: --listen`, carrying the declared signature `chat-listen-only:`.
    - M1.green: pass. With `access: listen` on the join record, `listeners` replayed in `groupState`, and `requireSpeaker` on post, membership changes, and archive, the listen-only member has the mention unread, `notice --check` exits 0, `ack` and `done` succeed, the four refusals name listen-only, and `group list` shows `review (listen)`. A first green attempt still accepted the post because `access` was missing from the record's `FIELD_ORDER`, so it was never written; adding it fixed that.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 251 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real CLI with three bound roles and reads unread JSON, the notice exit code, each command's exit code and stderr, and the group list.
      - Scope check: `git status --short` lists `src/core/chat/store.js`, `src/core/chat/cli.js`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: a Slack message from a user or bot mapped to a listen-only role is still imported as that role; the bridge maps people, not permissions, and a listen-only session posting through Slack is not a path this issue reported.
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
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirement is appended to `openspec/specs/keel-cross-host-mailbox/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:535db8703dc0951b0981853af17cfad2fe4d4bc98e48ef0ac2bbf073383df011
    - M1: pass. After merging `main` (5.107.0, #281; the README line both changes extended was merged by hand, keeping both sentences), `node scripts/bump_version.js minor` moved every marker to 5.108.0. With the 5.108.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-cross-host-mailbox/spec.md`; `published-specs-validate-strictly` reports `33 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published spec carries the requirement with its three scenarios, and the changelog names the issue, the decision, and each refusal.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after merging `main` and the bump to 5.108.0 reports `validation --all passed: baseline plus 252 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: A review session hears the user's own words in a shared group without being able to speak there (D1–D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
