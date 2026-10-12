# Tasks

## 1. Restate after tools

- [x] 1.1 A rate-limited PostToolUse hook restates the owner's language
  - Covers:
    - keel-owner-language / The owner's language is restated after runs of tool calls / The rule returns after a run of tool calls
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
    - F3
  - Read:
    - src/core/chat/notice.js
    - plugins/keel/scripts/mail-hook.js
  - Touch:
    - src/core/chat/notice.js
    - plugins/keel/scripts/mail-hook.js
    - .claude-plugin/plugin.json
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario owner-language-after-tools` declares `owner_language: zh`, submits a prompt for session `t1` through `plugins/keel/scripts/mail-hook.js user-prompt-submit`, then feeds `post-tool-use` 16 times, and requires calls 1–14 and 16 to print nothing and call 15 to print `additionalContext` with `中文`; after another prompt, call 1 prints nothing; a host-run session (first prompt `<scheduled-task …`) prints nothing on its 15th call; a repository without the declaration prints nothing; and `.claude-plugin/plugin.json` registers `PostToolUse` on `mail-hook.js post-tool-use`. Fails with: `owner-language-after-tools:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0865a84f22af6c52bbbba39bf3c57d1fa486ca23cda8bb3cca9ba35094f1ecc1
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario owner-language-after-tools` reports `owner-language-after-tools scenario passed.`
    - M1.red: fail. Before the change the scenario reported `owner-language-after-tools: .claude-plugin/plugin.json does not register PostToolUse on mail-hook.js post-tool-use: []`, carrying the declared signature `owner-language-after-tools:`.
    - M1.green: pass. With the PostToolUse registration, `post-tool-use` in `mail-hook.js`, `languageAfterTools`, and the reset on UserPromptSubmit: through `mail-hook.js`, calls 1–14 and 16 after a prompt print nothing and call 15 prints the rule with `中文`; after another prompt the first call prints nothing; a host-run session's 16 calls print nothing; a repository without `owner_language:` prints nothing.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 274 scenarios, 1 skipped: output-survives-the-pipe.`, including `native-plugin-manifests` with the PostToolUse entry expected.
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real plugin script `mail-hook.js` (which runs the real CLI) with host-shaped payloads, and reads the root manifest.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `plugins/keel/scripts/mail-hook.js`, `.claude-plugin/plugin.json`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: a host-injected status request that follows fewer than 15 tool calls inside 10 minutes still has no reminder beside it; the owner chose a bounded cadence over one per call.
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
    - openspec/specs/keel-owner-language/spec.md
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
    - M2: the ADDED requirement is appended to `openspec/specs/keel-owner-language/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e32be7ee001e3528ace9199c8a155a26cecec7290e314d8e459a4dbf2dacddc5
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.124.0; with the 5.124.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-owner-language/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the version markers, the changelog section, and the promoted spec are checked by the two scenarios, and the full suite passes on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the published spec, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "the chat hook restates it on every prompt" — `README.md` The owner's language, which now also restates it after runs of tool calls (the `keel/config.yaml` comment names only the places it lists and stays true). Updated by: 1.1

## Expectation Coverage

- E1: A reply the agent writes mid-turn, after a long run of tools, has the owner's language beside it too, at a bounded context cost (D1–D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.124.0 tree reports `validation --all passed: baseline plus 274 scenarios, 1 skipped: output-survives-the-pipe.`
