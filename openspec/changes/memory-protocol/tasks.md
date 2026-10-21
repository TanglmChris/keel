# Tasks

## 1. Put the memory rule into the protocol and the shift check

- [x] 1.1 Add the memory rule to the bootstrap and the full protocol, and a memory note to `keel shift check`
  - Covers:
    - keel-stateless-continuity / The bootstrap states what memory may hold and when it is rechecked / A fresh install carries the memory rule
    - keel-shift-change / The shift check reminds the session to recheck memory / A clean worktree is ready and is reminded about memory
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - D7
  - Read:
    - openspec/changes/memory-protocol/design.md
    - assets/bootstrap/AGENTS.md
    - scripts/validation/common.py
    - src/core/shift.js
  - Touch:
    - assets/bootstrap/AGENTS.md
    - scripts/validation/common.py
    - AGENTS.md
    - src/core/shift.js
    - plugins/keel/commands/shift.md
    - docs/shift-change.md
    - scripts/validation/shift.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario memory-rule-reaches-every-repo`: `keel --install` into an empty repository writes an `AGENTS.md` block that says memory holds only what the repository cannot answer and names a recheck at a shift change, within `BOOTSTRAP_BLOCK_BYTE_BUDGET`; `keel shift check` in a clean worktree bound to a role exits 0 as ready and carries the memory note in its text and in `--json` `notes`; and `plugins/keel/commands/shift.md` tells the session to act on it. Fails with: `memory-rule-reaches-every-repo:`
    - M2 (regression): the baseline (resident blocks within budget and topics), `--scenario thin-native-install`, `--scenario delegation-resident-text`, `--scenario shift-slash-command`, `--scenario shift-self` and `--group shift` pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:7ab482de04f19323285602de97f613135d5117b4063410eb3dd7f9c4e5777cf7 (keel 5.186.0)
    - M1: pass. `memory-rule-reaches-every-repo scenario passed.`
      - `keel --install` into an empty repository wrote a bootstrap whose memory bullet says memory holds only what "the repository cannot answer", and names a recheck "at a shift change". The block is within the 1700-byte budget: `assets/bootstrap/AGENTS.md` is 1602 bytes.
      - `keel shift check` in a clean bound worktree printed `keel shift check: ready` and a `note: memory: before the hand-off note, …` line, and exited 0. `--json` shows `ready: true`, no items, and the memory note in `notes`.
      - `/keel:shift` step 1 tells the session to act on the note.
    - M1.red: `memory-rule-reaches-every-repo: the installed bootstrap does not say memory holds only what the repository cannot answer: "<!-- keel:start v…`. This run used origin/main's `assets/bootstrap/AGENTS.md`, restored temporarily under the re-recorded fingerprint 7ab482de, and the same text was seen under the first fingerprint.
    - M1.green: `memory-rule-reaches-every-repo scenario passed.` These changes are now in place:
      - the bootstrap has the memory bullet;
      - the budget moves from 1400 to 1700, with the reason beside the constant;
      - `RESIDENT_BLOCKS` requires two memory topics;
      - `AGENTS.md` has a `## memory` section;
      - `check()` pushes the memory note;
      - `/keel:shift` and `docs/shift-change.md` mention the note.
    - M2: pass.
      - The baseline exits 0, so the resident blocks are within budget and carry their topics.
      - `thin-native-install`, `delegation-resident-text`, `shift-slash-command` and `shift-self` pass.
      - `--group shift` passes 47 scenarios.
    - Review:
      - Status: pass
      - Acceptance check: M1 goes through the public entry points a consuming repository meets: `keel --install` and its written `AGENTS.md`, `keel shift check` in text and JSON, and the shipped `/keel:shift` text. It asserts the rule's topics and the budget, and that readiness is unchanged.
      - Scope check:
        - The changed files are the eight in Touch, plus this change's record.
        - Keel reads no memory file: the note is a fixed string.
      - Findings:
        - The first green run showed the installed block at 1601 bytes, over the 1600 first chosen in D2. The budget was set to 1700 under a recorded reauthorization, matching the constant's own "plus one short clause" rule. Resolved here: M1
    - Blocker: none
    - Reauthorizations: 2026-10-21 14:40, before any Evidence was recorded. D2's budget changed from 1600 to 1700 in design.md. The first green run measured the installed block at 1601 bytes, so 1600 left no room for the rule at all, while the constant's comment asks for "current content plus one short clause". The fingerprint was re-recorded, and the red was re-run under it against origin/main's bootstrap.

## 2. Release

- [ ] 2.1 Release and promote the specs
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
    - openspec/specs/keel-stateless-continuity/spec.md
    - openspec/specs/keel-shift-change/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the deltas are promoted into `keel-stateless-continuity` and `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract:
    - M1:
    - M2:
    - M3:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: In `scripts/validation/common.py`, the bootstrap budget comment says "1400 rather than a round 1536: the headroom is 'current content plus one short clause'". Updated by: 1.1.
- I2: The bootstrap's only memory sentence is "memory or transcripts may only inform", in `assets/bootstrap/AGENTS.md`, which says nothing about what to write or when to recheck. Updated by: 1.1.

## Expectation Coverage

- E1: Every Keel repository's bootstrap tells the session what memory may hold and when to recheck it, and a shift check reminds it, while Keel reads no memory (#416; D1–D7). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
