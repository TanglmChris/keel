# Tasks

## 1. The digest

- [ ] 1.1 `keel chat summary --since` lists per group and sender what changed, folds superseded records, and names waiting acknowledgements
  - Covers:
    - keel-cross-host-mailbox / A structural digest summarizes what changed since a time / A coordinator's digest
    - keel-cross-host-mailbox / A structural digest summarizes what changed since a time / Nothing since the time
    - keel-cross-host-mailbox / A structural digest summarizes what changed since a time / A summary without a time or a role is refused
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
  - Touch:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - scripts/validate_plugin.py
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-summary` builds the coordinator's-digest fixture with roles `rtl` and `verify` and requires `keel chat summary --since <before> --json` to report it as the scenario describes, every read cursor file to be byte-identical before and after, a `--since` after the last record to say nothing changed with exit 0, and a missing `--since`, an unreadable one, and a worktree with no role each to exit non-zero naming the fix. Fails with: `chat-summary:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
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

- E1: A coordinator reads what changed since a time from one deterministic command, with superseded records folded and waiting acknowledgements named (D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
