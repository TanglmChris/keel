# Tasks

## 1. Shift history

- [x] 1.1 The hooks record each shift's transcript, and `keel shift history` lists and searches them
  - Covers:
    - keel-shift-change / A cleared shift's conversation stays findable / The previous shift's transcript is found after a clear
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - F1
    - F2
    - F3
    - F4
    - F5
  - Read:
    - src/core/chat/notice.js
    - src/core/shift.js
  - Touch:
    - src/core/chat/notice.js
    - src/core/shift.js
    - docs/shift-change.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-history` writes transcripts A, B, C as JSON lines in the host's shape, feeds `keel chat hook` a `session-start` and `user-prompt-submit` for `verify` with A, a `session-start` with source `clear` and B, and a scheduled run (`session-start` then a `<scheduled-task` prompt) with C, and requires: `keel shift history verify` listing B as current and A ended and not C; `--grep` for a phrase in A printing it under A and exiting 0, and for an absent phrase exiting 1; `--json` carrying both segments; `keel shift ready` by `verify` naming `keel shift history verify` and `Remote Control`; and, with `CLAUDE_CONFIG_DIR` pointing at a scratch directory holding transcripts D (an earlier conversation) and E (a scheduled run) under the `projects/` folder named for `verify`'s worktree, `keel shift history verify` listing D marked `(found)` and not E, and `--grep` for a phrase in D printing it. Fails with: `shift-history:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:73b721cc110b2a5156a67507b773c049d22f3f3d6b4952b2528e806b39b6515a
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-history` reports `shift-history scenario passed.`
    - M1.red: fail. Before the change the scenario reported `shift-history: ready does not name keel shift history verify: …`; after D6 was added, the extended scenario reported `shift-history: the earlier transcript D is not listed as found: …`. Both carry the declared signature `shift-history:`.
    - M1.green: pass. With `recordSegment`, the segments saved and restored beside presence, `keel shift history`, the transcript discovery, and the hint lines: history lists B current and A ended and not the scheduled run's C; `--grep "clock gate"` prints it under A and exits 0, an absent phrase exits 1; `--json` carries B then A; `ready` names `keel shift history verify` and `Remote Control`; with `CLAUDE_CONFIG_DIR` at a scratch directory, the earlier D is listed `(found)`, the scheduled run E is not, and `--grep "arbiter plan"` finds it in D. A first green attempt listed A before B because both were recorded in the same second; the recorded segments are now reversed before a stable sort. Run read-only in rtl_ppa_prj, `keel shift history iecc-pm` listed the PM's three transcripts (10-04, 10-06, 10-12) without the four patrol runs, and `--grep` found the 10-04 sentence the host's transcript search did not, once after duplicate records were folded.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 269 scenarios, 1 skipped: output-survives-the-pipe.` An earlier run failed `chat-bridge-inbound` (`a ✅ from a registered user did not close the todo.`); alone it then failed 1 of 15 runs on this branch, both failures under concurrent load, and passed 18 of 18 on clean main, a sample too small to separate. This change does not touch the bridge.
    - Review:
      - Status: pass
      - Acceptance check: the scenario feeds the real `keel chat hook` host-shaped payloads with transcript paths, writes transcripts in the host's JSON-lines shape, and reads `keel shift history` text, `--grep` exit codes, and `--json`.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `src/core/shift.js`, `docs/shift-change.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: `chat-bridge-inbound` failed twice under load and passed alone; it is not in this change's scope, and no failing run on main has been observed to file against yet. Discard reason: Codex transcripts are not read (D6); the owner's sessions in question are Claude's.
    - Blocker: none
    - Reauthorizations: 1. The owner asked mid-task on 2026-10-12 that earlier history be searchable too; D6, F5, the requirement sentence, and M1's last clause were added and the contract re-recorded with `task-start --record` before any Evidence was written.
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
    - openspec/specs/keel-shift-change/spec.md
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
    - M2: the ADDED requirement is appended to `openspec/specs/keel-shift-change/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:202edccd9ed2a47ec29a4b0323640b78b668a5db68c58c03d91ac7b371dc53e7
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.119.0; with the 5.119.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-shift-change/spec.md`; `published-specs-validate-strictly` reports `34 published specs validate strictly against openspec 1.14.0.`
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

- I1: "Now clear this session:" — the clear hint in `src/core/shift.js` and `docs/shift-change.md`, which say nothing of Remote Control blocking a clear or of where the cleared conversation goes. Updated by: 1.1

## Expectation Coverage

- E1: After a shift change the previous shift's conversation can be listed and searched by role, a scheduled run does not pollute that record, and a Remote Control session is told how to clear (D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.119.0 tree reports `validation --all passed: baseline plus 269 scenarios, 1 skipped: output-survives-the-pipe.`
