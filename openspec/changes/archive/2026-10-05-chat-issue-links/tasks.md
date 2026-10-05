# Tasks

## 1. Issue links

- [x] 1.1 Issue references link to GitHub in Slack and come back as text
  - Covers:
    - keel-chat-slack-bridge / Formatting is translated between Markdown and Slack mrkdwn / Issue references link to GitHub
    - keel-chat-slack-bridge / Formatting is translated between Markdown and Slack mrkdwn / A bare reference stays text without a GitHub origin
    - keel-chat-slack-bridge / Formatting is translated between Markdown and Slack mrkdwn / An issue link comes back as its text
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
    - F3
  - Read:
    - src/core/chat/mrkdwn.js
    - src/core/chat/bridge.js
  - Touch:
    - src/core/chat/mrkdwn.js
    - src/core/chat/bridge.js
    - scripts/validate_plugin.py
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-issue-links` sets the scratch project's `origin` to `git@github.com:acme/rtl.git`, posts `see #42, acme/other#7, C# and abc#9` plus `` `#5` `` through `keel chat bridge run --once`, and requires the posted text to contain `<https://github.com/acme/rtl/issues/42|#42>` and `<https://github.com/acme/other/issues/7|acme/other#7>`, keep `C#`, `abc#9`, and `` `#5` `` as text, and leave the record unchanged; removes `origin`, posts `see #43 and acme/other#8`, and requires `#43` unlinked and `acme/other#8` linked; pushes the owner's `<https://github.com/acme/rtl/issues/42|#42> done` to a running bridge and requires the imported text `#42 done`; and requires both setup guides to mention issue links. Fails with: `chat-issue-links:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-slack-format`, `chat-bridge-outbound`, and `chat-bridge-inbound` each pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f6ca23f3d8c212c48199b16dba216607d0f1edd563a25fdbb55d962f7022d892
    - Blocker: none
    - Reauthorizations: 2026-10-05 re-recorded from sha256:1c4b3f65… to sha256:f6ca23f3… after D3 was reworded during implementation to the boundary rule the code applies (no ASCII word character, `#`, `/`, `;`, `&`, `.`, or `-` before a reference), so CJK punctuation beside `#N` links; no check text changed, so M1, M2, and M3 were kept, and M1 and M2 were re-run after the rewording and pass.
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-issue-links` reports `chat-issue-links scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-issue-links: the posted text lacks '<https://github.com/acme/rtl/issues/42|#42>': 'see #42, acme/other#7, C# and abc#9 and `#5`'`, carrying the declared signature `chat-issue-links:`.
    - M1.green: pass. With `linkIssues` in `src/core/chat/mrkdwn.js` linking references outside code and outside existing links, `fromSlack` returning an issue link to its shown text, the bridge reading `owner/repo` from a GitHub `origin`, and one sentence in each guide, the same scenario passes. A manual check showed `#231` after `、`, `修复了#3`, and `**#5**` linked, and `issue#3`, `&#12;`, `C#`, and `a.b#1` left alone, each round-tripping to its original text.
    - M2: pass. `chat-slack-format`, `chat-bridge-outbound`, and `chat-bridge-inbound` each report `scenario passed.`
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario reads the text the fake server received for a project with and without a GitHub origin, the unchanged record, and the record imported from the owner's link, and reads both guides.
      - Scope check: `git status --short` lists `src/core/chat/mrkdwn.js`, `src/core/chat/bridge.js`, `scripts/validate_plugin.py`, and both setup guides, all in Touch, plus this change's own directory.
      - Findings: Discard reason: a bare `#N` always means the posting project's repository, so a session in rtl_ppa_prj that writes `#226` meaning a Keel issue gets an rtl_ppa_prj link; writing `TanglmChris/keel#226` is the documented way to name another repository, and guessing from context would link wrongly more often than it helps.

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
    - M1: `node scripts/bump_version.js minor` moves every marker to 5.96.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.96.0 section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1e79227f9761bf7f5693c9b9e268a7f58771d547fb2cbab8dda5c7e16966beac
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.96.0. With the 5.96.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its published copy, keeping its two scenarios and adding three; `published-specs-validate-strictly` reports `30 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the promoted requirement carries the issue-link clauses and scenarios, and the changelog names both directions and the guide sentence.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the promoted spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump reports `validation --all passed: baseline plus 235 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: An issue a session mentions in Slack is a link that opens it on GitHub. Covered by: 1.1, 2.1
