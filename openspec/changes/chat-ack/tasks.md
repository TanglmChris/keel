# Tasks

## 1. Acknowledgements

- [ ] 1.1 `--ack`, `keel chat ack`, replies as acknowledgements, and who has acknowledged in `show` and `acks`
  - Covers:
    - keel-cross-host-mailbox / A record can ask for an acknowledgement, and who has given it is listed / A sender sees who has not acknowledged
    - keel-cross-host-mailbox / A record can ask for an acknowledgement, and who has given it is listed / A reply acknowledges
    - keel-cross-host-mailbox / A record can ask for an acknowledgement, and who has given it is listed / Acknowledging is refused where it means nothing
    - keel-cross-host-mailbox / A record can ask for an acknowledgement, and who has given it is listed / An acknowledgement wakes nobody and is marked where it is asked
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
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - src/core/chat/view.js
    - src/core/chat/notice.js
    - src/core/chat/bridge.js
  - Touch:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - src/core/chat/view.js
    - src/core/chat/notice.js
    - src/core/chat/bridge.js
    - scripts/validate_plugin.py
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-ack` runs, with roles `rtl`, `verify`, and `spec` in one group, every keel-cross-host-mailbox acknowledgement scenario through the real CLI: `show --json` and `acks --mine --json` lists after `verify` acknowledges and `spec` only reads; `spec`'s reply moving it to acknowledged and the record leaving `acks`; each refusal exiting non-zero naming why; `rtl`'s unread holding nothing from the acknowledgement; and `(ack requested)` in `spec`'s group view and wake notice. Fails with: `chat-ack:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-outbound` adds an acknowledged `--ack` record and requires no Slack call carrying the acknowledgement's id. Fails with: `chat-bridge-outbound:`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: pending
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirement is appended to `openspec/specs/keel-cross-host-mailbox/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
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

- None.

## Expectation Coverage

- E1: A sender can ask for and see acknowledgements, so silence no longer has to be read as work in progress (D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
