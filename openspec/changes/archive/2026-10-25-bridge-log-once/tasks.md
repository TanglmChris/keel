# Tasks

## 1. Log a repeating failure once, and name the missing scope

- [x] 1.1 The bridge logs a repeating archive or catch-up failure once, and a Slack error names the needed scope
  - Covers:
    - keel-chat-slack-bridge / The bridge logs a repeating failure once and names a missing scope / A refusal that never changes is logged once
    - keel-chat-slack-bridge / The bridge logs a repeating failure once and names a missing scope / A missing scope is named once across reconnects
    - D1
    - D2
    - D3
    - D4
  - Read:
    - openspec/changes/bridge-log-once/design.md
    - src/core/chat/bridge.js
    - src/core/chat/slack.js
    - scripts/fake_slack.py
  - Touch:
    - src/core/chat/bridge.js
    - src/core/chat/slack.js
    - scripts/fake_slack.py
    - scripts/validation/chat.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-logs-once`: against the fake Slack, a running `keel chat bridge run` with `KEEL_CHAT_ARCHIVE_EVERY_MS=300` on a Slack-enabled project with no remote logs `this repository has no remote` once over at least five syncs; with `conversations.history` answering `missing_scope` and `needed: channels:history`, three reconnects leave one `catch-up failed` line naming `missing_scope: needs channels:history`; after the server answers normally and the bridge reconnects, one `catch-up works again` line. Fails with: `chat-bridge-logs-once: the archive refusal was logged`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group chat --jobs 4` passes, and so does `--scenario assertion-shape-count`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:15d06434f58adffe9c795dba9f8e721d783dab3f8c811640146bc7ba318d1f2a (keel 5.199.0)
    - M1: pass. `chat-bridge-logs-once scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `chat-bridge-logs-once: the archive refusal was logged 0 times over syncs every 300 ms, not once: 'keel chat bridge: catch-up failed: Slack conversations.history failed: missing_scope (HTTP 200)\nkeel chat bridge: catch-up failed: …` (exit 1). The interval seam did not exist, so no sync ran, and each of the four connects logged the same catch-up failure, which named no scope.
      - A first run failed earlier, with `the bridge did not catch up after the scope was granted`. The fourth reconnect waits 16 s under the doubling backoff, longer than the scenario's 15 s wait. The wait is now 30 s, and the comment says why.
    - M1.green: pass.
      - `onceLog` on the bridge context logs a key's line only when it differs from the last one, and logs one recovery line when the key clears (D1).
      - The archive timer keys on `archive:<project>`, and the hello handler on `catch-up:<role>`.
      - `SlackError` keeps `needed` and `provided`, and its message reads `missing_scope: needs channels:history` (D2).
      - `KEEL_CHAT_ARCHIVE_EVERY_MS` sets the interval (D3). `FakeSlack.fail` answers a method with a chosen body (D4).
    - M2: pass. `validation --group chat passed: 48 scenarios.` (exit 0, run at load 9). `assertion-shape-count scenario passed: 74 sites`.
    - Review:
      - Status: pass
      - Acceptance check: through a real running `keel chat bridge run` against the fake Slack, the no-remote refusal appears once across at least six syncs. Four connects that fail with `missing_scope` log one line, and it names `needs channels:history`. After the scope is granted, one `catch-up works again` line follows.
      - Scope check: `git status --short` lists `src/core/chat/bridge.js`, `src/core/chat/slack.js`, `scripts/fake_slack.py`, `scripts/validation/chat.py`, `scripts/validation/registry.py`, and this change's directory, all in Touch. `.DS_Store` is untracked Finder metadata that predates the change.
      - Findings: none.
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
    - openspec/specs/keel-chat-slack-bridge/spec.md
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
    - M2: the delta is promoted into `keel-chat-slack-bridge`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ca6344ea177577f6938f03d0a31ee324e73774ca8f26407a93725f04b82d5a49 (keel 5.199.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.199.0 → 5.200.0. With the section "The bridge logs a repeating failure once and names a missing scope" written, `version-alignment scenario passed.` (exit 0).
    - M2: the added requirement "The bridge logs a repeating failure once and names a missing scope" is promoted into `keel-chat-slack-bridge`. `published-specs-validate-strictly scenario passed: 34 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test` on commit 42888a6d (clean tree), started 19:06 at load 8.43: `validation --all passed: baseline plus 337 scenarios, 2 skipped: output-survives-the-pipe, docx-converts-markdown-with-svg.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2. The markers, the 5.200.0 section, and the published spec carry the change, and the full suite passes on the committed tree.
      - Scope check: beyond task 1.1, the files are the version markers, `keel/CHANGELOG.md`, and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: A failure that repeats unchanged is logged once, its recovery once, and a missing Slack scope is named (#460; D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
