# Tasks

## 1. A shift's conversation is kept

- [x] 1.1 Copy ended segments into Keel's store; `history` and `--grep` read the copy; `--grep` reads Codex rollouts
  - Covers:
    - keel-shift-change / A cleared shift's conversation stays findable / A shift's conversation outlives the host's file
    - keel-shift-change / A cleared shift's conversation stays findable / A Codex rollout is searched
    - D1
    - D2
    - D3
    - D4
    - D5
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-keeps-transcripts` runs the real chat hook and CLI in a scratch repository: `verify`'s session-start in transcript A and then in transcript B leaves a gzip copy of A, byte-identical after decompression, under `<store>/shift/transcripts/verify/` and no copy of B; after A is deleted, `keel shift history verify` lists A with `(kept)` and not `(missing)`, and `--grep` finds a phrase said in A and exits 0; a segment whose transcript is a Codex rollout with a user `input_text` phrase is found by `--grep`; A grown after its copy is copied again at the next segment change. Fails with: `no kept copy of transcript A`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-history` and `--scenario chat-archive` still pass.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:fb4f4b2c5d862e872289f95ed2584ecb146df74d863ac4571f2b1086810ab187 (keel 5.142.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-keeps-transcripts` reports `shift-keeps-transcripts scenario passed.`
    - M1.red: fail. With the scenario written first: `shift-keeps-transcripts: no kept copy of transcript A under …/rtl/.git/keel-chat/shift/transcripts/verify: no directory`, carrying the declared signature `no kept copy of transcript A`.
    - M1.green: pass. With `keepEnded` in `recordSegment` (gzip copy of each ended, existing segment whose copy is missing or whose size/mtime moved, through a temporary file and rename; `kept` and `kept_from` on the segment), `history` reading the copy and marking `(kept)`, `readTranscript` decompressing it, and `conversationLine` reading Codex `response_item` messages, the scenario passed. (A middle run failed on `(missing)` until `history` read the copy.)
    - M2: pass. `--scenario shift-history` and `--scenario chat-archive` each report `scenario passed.`
    - M3: pass. `npm test`: `validation --all passed: baseline plus 287 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0). The first run failed `assertion-shape-count` (82 vs 80 sites) on `or`-joined checks in the new scenario; each was split so every failure carries its own message.
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real chat hook and `keel shift history` in a scratch repository: A's gzip copy equals A's bytes and B, still current, has none; with A deleted, history marks it `(kept)` and `--grep` prints its phrase; a Codex rollout's `input_text` is found; B grown after its copy is copied again. Beyond the checks: gzip of keel-maint's 9 ended transcripts took 609 ms (19.2 MB → 3.9 MB), inside the hook's 10 s; a real `codex exec` recorded its rollout as the segment (design F4).
      - Scope check: `git status --short` lists `docs/shift-change.md`, `scripts/validate_plugin.py`, `src/core/chat/notice.js`, `src/core/shift.js`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: transcripts `history` finds in Claude's project directory without a recorded segment (#304 D6) are not copied; only segments the hooks recorded are, and every bound role records from its first hook call.
        - Discard reason: a host-run session restores the segments file it replaced (#304 D2), which can drop a `kept_from` written during that run; the copy stays on disk and the next segment change copies again, so the cost is one repeated copy.
        - Discard reason: Codex keeps its rollout files without a cleanup period we know of, so its copies are insurance rather than rescue; covered at no extra cost because the same hook records them.
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
    - Contract: keel-task-capsule/v1 sha256:22f6203fdd9e006745a17c2b60c7b360a753c767f8cbe85148e02f4ec0cfbf1e (keel 5.142.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.142.0 → 5.143.0; with the "A shift's conversation is kept, not only pointed at" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the MODIFIED requirement replaced its counterpart in `keel-shift-change`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`keel shift history <role>` lists those transcripts" — `docs/shift-change.md`, which says nothing of Keel keeping a copy. Updated by: 1.1
- I2: "`keel shift history [<role>]` MUST list the role's transcript segments" with no copy — `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: A shift's full conversation survives the host deleting its transcript, for Claude and Codex, and `--grep` still finds it (#343, D1, D3, D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
