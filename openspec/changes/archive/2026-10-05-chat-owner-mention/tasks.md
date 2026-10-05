# Tasks

## 1. Owner mention rule

- [x] 1.1 The session-start notice states the owner-mention rule
  - Covers:
    - keel-chat-slack-bridge / The bridge runs unattended but stays visible and controllable / The session learns to mention the owner
    - D1
    - D2
    - D3
    - F1
    - F3
  - Read:
    - src/core/chat/notice.js
    - src/core/chat/bridge.js
  - Touch:
    - src/core/chat/notice.js
    - scripts/validate_plugin.py
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-owner-mention` runs the SessionStart chat hook for a bound role in a Slack-enabled project with `slack.owner` set and requires its notice to contain `@owner` and `decide`; runs it again after removing `owner` from `keel/chat.json` and requires no `@owner`; posts a record containing `@owner` through `keel chat bridge run --once` against the fake Slack server and requires the posted text to begin with `<@UOWNER>`; and requires both setup guides to state the rule. Fails with: `chat-owner-mention:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-lifecycle` and `chat-claude-hooks` each pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4be3cad42a59b857d5b169a924d9827b0a4090903ddfcfadc4842059c96524ce
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-owner-mention` reports `chat-owner-mention scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-owner-mention: the session-start notice does not tell the session to write @owner: 'keel chat bridge: not running on this machine, …'`, carrying the declared signature `chat-owner-mention:`.
    - M1.green: pass. With `bridgeLine` appending the owner rule when `slack.owner` is set, and one sentence beside the `owner` field in each setup guide, the same scenario passes.
    - M2: pass. `chat-bridge-lifecycle` and `chat-claude-hooks` each report `scenario passed.`
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario reads the real SessionStart hook output with and without an owner named, posts an `@owner` record through the bridge to the fake server and reads the mention, and reads both guides.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `scripts/validate_plugin.py`, and both setup guides, all in Touch, plus this change's own directory.
      - Findings: Discard reason: the rule reaches a running session only at its next session start, `/compact`, or `/clear`, because the notice is session-start text; the sessions are told by chat message when the release is installed, which is a one-off notice rather than product work.

## 2. Release

- [x] 2.1 Release and promote the spec
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
    - M1: `node scripts/bump_version.js patch` moves every marker to 5.95.3, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.95.3 section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:542c3a1b5f9db47944a2f445c160a7112a51bd2e40d149caf52024bbf4d45161
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js patch` moved every marker to 5.95.3. With the 5.95.3 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its published copy, keeping its six scenarios and adding the new one; `published-specs-validate-strictly` reports `30 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the promoted requirement carries the owner-rule clause and scenario, and the changelog states the rule and when running sessions see it.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the promoted spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. The first `npm test` after the bump failed only `chat-bridge-inbound` (`the owner's mention did not touch verify's signal file.`), a timing race in that scenario owned by https://github.com/TanglmChris/keel/issues/231; three standalone runs passed, and the rerun `npm test` reports `validation --all passed: baseline plus 234 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: A Slack message the owner needs to know about mentions them, so Slack notifies them. Covered by: 1.1, 2.1
