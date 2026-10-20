# Tasks

## 1. Retention counts only sessions with a conversation

- [x] 1.1 Count toward `keep_old_sessions` only a session whose transcript is in the host's files or Keel's store
  - Covers:
    - keel-shift-change / A CLI session changes its own shift and the next one is named for its start / Only the newest old sessions stay listed
    - D1
    - D2
  - Read:
    - src/core/shift.js
    - openspec/changes/shift-retention-counts-conversations/design.md
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-keeps-old-sessions`: with `keep_old_sessions: 2`, a session with no transcript that is newer than the other old ones, and the oldest with only Keel's copy, the removed sessions are exactly the three oldest with a transcript, the copy-only one included; the session with no transcript stays. Fails with: `not the oldest beyond the two newest with a transcript`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f8304438396461245fee0bfb8e8fc8f37626d5415cb05f5da4f2feaddfebf1ae (keel 5.168.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-keeps-old-sessions` reports `shift-cli-keeps-old-sessions scenario passed.`: with `keep_old_sessions: 2` the removed sessions were `01010101` (Keel's copy only), `02020202` and `03030303`; `06060606` (no transcript, newer than the others), `04040404`, rtl's session, the new session and the one handed over stayed.
    - M1.red: fail. With the scenario's sessions and 5.168.0's `removeOldSessions`: `shift-cli-keeps-old-sessions: with keep_old_sessions 2 the removed sessions are ['02020202', '03030303', '04040404'], not the oldest beyond the two newest with a transcript.`
    - M1.green: pass. With `removeOldSessions` counting only rows that have a host transcript or Keel's copy at `keptFile(…, <session>.jsonl)`, and removing a copy-only row without rewriting the copy, the scenario passed; `shift-cli-self-shift` and `shift-history-show` pass too.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 307 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: through `keel shift ready --wake` and `keel tick` against a fake `claude`, a never-prompted session newer than the old shifts no longer takes a kept slot, the two newest sessions with a transcript stay, and the older ones, a copy-only one included, are removed after Keel holds their copy.
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md` and this change's directory, all in Touch or the record layer.
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
    - M2: the delta requirement is promoted into `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b5286e702245992d100cef739467eafccfa20cae43dc40fcc6f6524ce4a6cda2 (keel 5.168.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.168.0 → 5.169.0; with the "CLI retention counts only sessions with a conversation" section written into the stub the bump left, `version-alignment scenario passed.` (exit 0).
    - M2: the MODIFIED requirement replaced its published text in place in `keel-shift-change`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "the newest `keep_old_sessions` of the role's stopped sessions" and "one whose transcript cannot be found stays" — `docs/cli-team.md`, and「该角色最新的 `keep_old_sessions` 个已停会话」「找不到 transcript 的会话保留不动」in `docs/cli-team.zh-CN.md`. Updated by: 1.1.
- I2: "keep the newest `shift: keep_old_sessions:` (default 3) stopped background sessions" — the CLI requirement in `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1.

## Expectation Coverage

- E1: `keep_old_sessions` keeps that many real shifts; a session that was never given a prompt does not use up a slot (#401; D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
