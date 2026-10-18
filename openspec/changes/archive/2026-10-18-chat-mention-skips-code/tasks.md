# Tasks

## 1. Quoted text and commit ids are not mentions

- [x] 1.1 Skip code spans, fenced blocks and unresolved commit ids in the mention scan
  - Covers:
    - keel-cross-host-mailbox / Groups have maintained membership, direct groups, and archive / A commit id or quoted text is not a mention
    - D1
    - D2
  - Read:
    - src/core/chat/store.js
    - src/core/chat/bridge.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/chat/store.js
    - src/core/chat/bridge.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-mention-skips-code` runs the real `keel chat post soc … --json` in a two-role group: posts carrying `@638059e4`, a 40-digit `@<sha>`, `` `@verifyy` `` and a fenced `@nobody` are each written with no mentions; a bare `@verifyy` is refused naming it; `` `@nobody` `` beside `@verify` records `["verify"]`. Fails with: `a post with commit-id was refused`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3ce8be73f8f3530a3c6d156b1abbe29c20105ca3787220949059d33177dddbe7 (keel 5.147.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-mention-skips-code` reports `chat-mention-skips-code scenario passed.`
    - M1.red: fail. With the scenario written first and the store unchanged: `chat-mention-skips-code: a post with commit-id was refused: '' 'keel chat: @638059e4 is not a member or alias in group soc.\n'`, #345's refusal, carrying the declared signature.
    - M1.green: pass. With `mentionText` blanking fenced blocks and inline code before both mention scans, and an unresolved 7–40 hex-digit token skipped, the scenario passed.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 292 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit. An earlier run failed `assertion-shape-count` on two combined checks in the new scenario; each was split.
    - Review:
      - Status: pass
      - Acceptance check: the real `keel chat post` writes posts with a short and a full commit id, an inline-code `@verifyy` and a fenced `@nobody` with no mentions; a bare `@verifyy` is still refused naming it; quoted `@nobody` beside `@verify` records only `verify`.
      - Scope check: `git status --short` lists `src/core/chat/store.js`, `src/core/chat/bridge.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: a role whose name is 7–40 hex digits and is not in the group would now be skipped rather than refused; no role in the stores here has such a name, and one that is a member is still a mention.
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta requirements are promoted into `keel-cross-host-mailbox`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:442c8b62f3f200dd213e822831f6bcca465d881b544503ec0c53503c0e802dd8 (keel 5.147.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.148.0 → 5.149.0; with the "A commit id or quoted @word is not a mention" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-cross-host-mailbox`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "a mention of a role that is neither a member nor an alias MUST be refused by name" with no exception for quoted text or commit ids — `openspec/specs/keel-cross-host-mailbox/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: A message citing a commit id or quoting an `@word` posts, and a typo is still refused (#345, D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
