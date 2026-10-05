# Tasks

## 1. Shared app direct messages

- [x] 1.1 The shared app takes direct messages for the one role it is mapped to
  - Covers:
    - keel-chat-slack-bridge / A role's app takes direct messages / The shared app takes direct messages for the role it is mapped to
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
  - Read:
    - src/core/chat/bridge.js
  - Touch:
    - src/core/chat/bridge.js
    - src/core/chat/cli.js
    - scripts/validate_plugin.py
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-shared-app-direct` maps the shared bot user `UBOT` to `rtl` in `slack.bots`, starts the bridge, pushes on the shared connection a direct message from `UOWNER`, and requires a record from `owner` in `dm-owner--rtl`; requires `keel chat dm owner` from `rtl` to reach `DUOWNER` once with `Bearer xoxb-test-bot`; requires exactly one connection with the shared app token; requires `keel chat bridge status --json` to report the shared app's direct messages as connected; and requires both setup guides to name `im:history`. Fails with: `chat-shared-app-direct:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-direct`, `chat-shared-bots`, `chat-bridge-inbound`, and `chat-bridge-outbound` each pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d1b2accb73d9aabef019b003dc56cace43ebf0cd8d9ea70a24bfa5a74c3c817c
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-shared-app-direct` reports `chat-shared-app-direct scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-shared-app-direct: the owner's direct message to the shared app did not reach dm-owner--rtl.`, carrying the declared signature `chat-shared-app-direct:`.
    - M1.green: pass. With `verifyBots` adding the shared app as a bot when a project maps its user, `handleEvent` passing `im` events to the direct handler, the shared hello catching up its direct channels, `connections` opening no second connection, status reporting it, and a paragraph in each guide, the same scenario passes. The scenario's two `or` conditions were split so that `assertion-shape-count` stays at 80.
    - M2: pass. `chat-role-direct`, `chat-shared-bots`, `chat-bridge-inbound`, and `chat-bridge-outbound` each report `scenario passed.`
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario pushes a direct message on the shared connection and reads the record, the posted answer with its token and channel, the count of connections with the shared app token, and the status entry, and reads both guides.
      - Scope check: `git status --short` lists `src/core/chat/bridge.js`, `scripts/validate_plugin.py`, and both setup guides, all in Touch, plus this change's own directory. `src/core/chat/cli.js` needed no change, because the status text already prints every entry of `bots`.
      - Findings: Discard reason: the scopes the real shared app needs (F3) are a Slack-side setting the owner changes; the guides state them, and the live check runs once the owner has reinstalled the app.

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
    - openspec/specs/keel-chat-slack-bridge/spec.md
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
    - M1: `node scripts/bump_version.js minor` moves every marker to 5.97.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.97.0 section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:cdeec995768d903976c65e77e780a1e2b483a09303b09735a0941a92a56aeb88
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.97.0. With the 5.97.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its published copy, keeping its scenarios and adding one; `published-specs-validate-strictly` reports `30 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the promoted requirement carries the shared-app clause and scenario, and the changelog names the mapping, the one-role rule, and the Slack-side scopes.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the promoted spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump reports `validation --all passed: baseline plus 237 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "direct messages work only for a bot that serves exactly one role" as said of registered bots only — the setup guides' bot section. Updated by: 1.1

## Expectation Coverage

- E1: The owner can message the Keel maintenance session through the shared app (D1, D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
