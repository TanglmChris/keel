# Tasks

## 1. A rename keeps a membership the new name already had

- [x] 1.1 Compute membership under the written names, then map it through the renames
  - Covers:
    - keel-cross-host-mailbox / A role can be renamed / A leave of the old name after the new one joined keeps the new one
    - D1
    - D2
  - Read:
    - src/core/chat/store.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/chat/store.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-rename` adds kaiwu-ip's order to its second repository — `check` added to `soc`, then `verify` removed — and after `keel chat role --rename verify check` requires `keel chat group list --json` to show `check` in `soc`, beside the scenario's existing assertions. Fails with: `removed check from soc`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:69559900fa79fe969ad4aa1d164322f50ef5178ffecfa1e265f69351aa45b2cf (keel 5.158.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-rename` reports `chat-role-rename scenario passed.`
    - M1.red: fail. With the assertion added and 5.159.0's code unchanged: `chat-role-rename: the old name's leave after the new one joined removed check from soc: [{'name': 'soc', 'members': ['rtl'], …}]`, carrying the declared signature. The same fault was first seen on a copy of kaiwu-ip's chat store: after `--rename iecc-pm kaiwu-pm-iecc`, `kaiwu-pm-iecc` had left `iecc` and its one unread record was gone.
    - M1.green: pass. With `readLog` giving `join`/`leave` records `member` and keeping `target`, and `groupState` mapping the replayed members — listen-only only when every merged name was — the scenario passed. On a fresh copy of kaiwu-ip's store the same rename kept the unread record (1 before, 1 after), and `kaiwu-pm-iecc` was then in `iecc`, `dmc-iecc` and every direct group `iecc-pm` had been in, with no `iecc-pm` member and no listener left.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 302 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: a leave of `verify` written after `check` joined `soc` no longer removes `check` once `verify` is renamed to `check`; the scenario's other assertions still hold.
      - Scope check: `git status --short` lists `src/core/chat/store.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
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
    - Contract: keel-task-capsule/v1 sha256:a80d5470a8cc543e4df0cd4de9e25f87245b769a5f294656ec082d048cc470dc (keel 5.158.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.159.0 → 5.160.0; with the "a rename keeps a membership the new name already had" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-cross-host-mailbox`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: A role renamed after a hand migration keeps the groups the new name had joined, as kaiwu-ip's did (D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
