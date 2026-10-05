# Tasks

## 1. Formatting

- [x] 1.1 Translate formatting between Markdown and Slack mrkdwn
  - Covers:
    - keel-chat-slack-bridge / Formatting is translated between Markdown and Slack mrkdwn / Markdown is sent as mrkdwn
    - keel-chat-slack-bridge / Formatting is translated between Markdown and Slack mrkdwn / A person's mrkdwn is stored as Markdown
    - D1
    - D2
    - D3
    - F1
    - F2
  - Read:
    - src/core/chat/bridge.js
  - Touch:
    - src/core/chat/mrkdwn.js
    - src/core/chat/bridge.js
    - scripts/validate_plugin.py
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-slack-format` posts a message with `**must**`, `*soon*`, `# Plan`, `- item`, `[spec](https://example.com/s)`, `` `a**b` ``, a fenced block containing `**raw**`, and `x<y&z` through `keel chat bridge run --once`, and requires the posted text to contain `*must*`, `_soon_`, `*Plan*`, `• item`, `<https://example.com/s|spec>`, `` `a**b` ``, `**raw**` inside the fence, and `x&lt;y&amp;z`, with the local record unchanged; then pushes the owner's `*urgent* _today_ ~old~ see <https://example.com|this> a &lt; b` to a running bridge and requires the imported text `**urgent** *today* ~~old~~ see [this](https://example.com) a < b`; and requires both setup guides to say sessions may format with Markdown. Fails with: `chat-slack-format:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-outbound`, `chat-bridge-inbound`, `chat-role-apps`, and `chat-shared-bots` each pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ac32022b6313755ed0a963365a039b870a2f509b44b462f7d4194bf4fcc806e5
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-slack-format` reports `chat-slack-format scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-slack-format: the posted text lacks '*Plan*': '# Plan\n**must** land *soon*...'`, carrying the declared signature `chat-slack-format:`.
    - M1.green: pass. With `src/core/chat/mrkdwn.js` translating outside code in both directions, `slackText` translating after redaction and before the cut, inbound person and bot text translated back, and one line in each setup guide, the same scenario passes. A manual check of snake_case names, paths, `2*3*4`, `->`, and `[redacted]` showed them unchanged apart from the required `&gt;` escape.
    - M2: pass. `chat-bridge-outbound`, `chat-bridge-inbound`, `chat-role-apps`, and `chat-shared-bots` each report `scenario passed.`
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario reads the text the fake server received and the record the running bridge wrote, covering each translated form in both directions plus code left alone and the local record unchanged.
      - Scope check: `git status --short` lists `src/core/chat/mrkdwn.js`, `src/core/chat/bridge.js`, `scripts/validate_plugin.py`, and both setup guides, all in Touch, plus this change's own directory.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/187 — whether Slack renders `*bold*` directly beside CJK text is unverified against real Slack; check with the first real post and record it on #187.

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
    - M1: `node scripts/bump_version.js minor` moves every marker to 5.95.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.95.0 section written.
    - M2: the ADDED requirement is promoted into `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
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

- E1: A session's Markdown shows as formatting in Slack, and a person's Slack formatting is stored as Markdown. Covered by: 1.1, 2.1
