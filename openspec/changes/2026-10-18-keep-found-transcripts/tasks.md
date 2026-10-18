# Tasks

## 1. Found transcripts are kept and read

- [x] 1.1 Keep found transcripts at a segment change; `history` reads a copy at the kept path without a record
  - Covers:
    - keel-shift-change / A cleared shift's conversation stays findable / A found transcript is kept and read after its file is gone
    - D1
    - D2
  - Read:
    - src/core/chat/notice.js
    - src/core/shift.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/chat/notice.js
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/shift-change.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-keeps-found-transcripts` drives the real chat hooks and `keel shift history` with `CLAUDE_CONFIG_DIR` pointing at a project directory for the bound worktree that holds an unrecorded transcript O and a scheduled run P: after two segment changes the store holds O's bytes gzip-compressed and no copy of P or of the current transcript; with O deleted, `history` lists O `(kept)`, not `(missing)`, and `--grep` prints a phrase said only in O. Fails with: `left the found transcript unkept`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-keeps-transcripts` and `--scenario shift-history` still pass.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:74cf5f30b9915d2473c89cc7ab6a21a8a623e7f5a1376ac06514bd593c9091d1 (keel 5.144.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-keeps-found-transcripts` reports `shift-keeps-found-transcripts scenario passed.`
    - M1.red: fail. With the scenario written first and the hook unchanged: `shift-keeps-found-transcripts: a segment change left the found transcript unkept: ['a.jsonl.gz']`, carrying the declared signature `left the found transcript unkept`.
    - M1.green: pass. A first implementation copied found transcripts but did not record them, and the scenario failed on `is not listed (kept)`: `history` finds only files that exist, so a deleted found transcript vanished from the list. With `keepFound` recording each found transcript (still `found`, with `kept` and `kept_from`) before the current segment, and `history` also looking at `keptFile` for a segment whose record names no copy, the scenario passed, including a third segment change that leaves the found transcript listed once.
    - M2: pass. `--scenario shift-keeps-transcripts` and `--scenario shift-history` each report `scenario passed.`
    - M3: pass. `npm test`: `validation --all passed: baseline plus 289 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real chat hooks and `keel shift history` against a Claude project directory for the bound worktree: the unrecorded transcript O is copied byte-for-byte at the next segment change, the scheduled run P and the current transcript are not, O deleted reads `(kept)` and its phrase is found by `--grep`, and another segment change lists O once.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `src/core/shift.js`, `scripts/validate_plugin.py`, `docs/shift-change.md`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: a found transcript is now parsed once at the segment change that first records it, so the first shift change after this release reads every unrecorded transcript of the role's worktrees (22 MB for keel-maint); later changes read none of them.
        - Discard reason: the two keel-maint copies made by hand on 2026-10-18 are left as they are, being newer than their transcripts; this path is exercised by the freshness test but not by a separate check.
    - Blocker: none
    - Reauthorizations: 2026-10-18 — D1 in design.md was rewritten during implementation, from copying found transcripts to copying and recording them, after the first implementation showed a deleted found transcript drops out of `history`; anchor re-recorded from sha256:3326525… to sha256:74cf5f3… with `--keep-evidence M1,M2,M3`, because M1, M2 and M3 were all run after that rewrite and the check texts did not move.

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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the MODIFIED requirement replaces its counterpart in `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract:
    - M1:
    - M2:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "When a role's session starts a new transcript, the hook MUST copy each ended segment's transcript" with no rule for a found transcript, and "`history` MUST read Keel's copy" read only through a record — `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1
- I2: "the hook copies each ended one into Keel's store" with no mention of found transcripts — `docs/shift-change.md`. Updated by: 1.1

## Expectation Coverage

- E1: Every conversation `history` lists for a role, recorded or found, outlives the host's file (#361, D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
