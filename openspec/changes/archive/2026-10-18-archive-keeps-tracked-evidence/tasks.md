# Tasks

## 1. An archive keeps the files the change tracked

- [x] 1.1 Re-add tracked files the archive move leaves ignored; warn at change-close
  - Covers:
    - keel-openspec-surface-overlay / An archive keeps the files the change tracked / Tracked evidence the change ignores survives the archive
    - keel-openspec-surface-overlay / An archive keeps the files the change tracked / The close warns before the move
    - D1
    - D2
  - Read:
    - bin/keel.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Touch:
    - bin/keel.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario archive-keeps-tracked-evidence` builds a Git repository initialized by `keel --init`, with a change whose own `.gitignore` ignores `evidence/**` and a force-added, committed `evidence/run.log`: `keel gate change-close --action archive --json` warns naming `evidence/run.log` and `keel openspec archive`; the real `keel openspec archive demo --yes --skip-specs` then exits 0, the archived `evidence/run.log` is in `git ls-files`, and the output says `re-added 1`. Fails with: `does not warn about tracked evidence the change ignores`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4c8b872f21c0e97dd625f763187f1d655583e0b17c74e9aca1dcdf3db8b3e92c (keel 5.147.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario archive-keeps-tracked-evidence` reports `archive-keeps-tracked-evidence scenario passed.`
    - M1.red: fail. With the scenario written first and the code unchanged: `archive-keeps-tracked-evidence: change-close --action archive does not warn about tracked evidence the change ignores: []`, carrying the declared signature. With only the gate warning in place and `bin/keel.js` reverted: `the archived evidence openspec/changes/archive/2026-10-18-demo/evidence/run.log dropped out of version control`, which is #352's loss reproduced through the real `keel openspec archive`.
    - M1.green: pass. With `trackedButIgnored` feeding a change-close warning and the passthrough recording tracked files before `archive` and running `git add -f` on those the archived path leaves ignored, the scenario passed.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 292 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: in a real Git repository initialized by `keel --init`, change-close warns naming the tracked, ignored `evidence/run.log` and `keel openspec archive`; the real archive then leaves its archived path in `git ls-files` and says `re-added 1`.
      - Scope check: `git status --short` lists `bin/keel.js`, `src/core/gates.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: an archive done with a bare `mv` or `openspec archive` is not repaired; the overlay already directs agents to `keel openspec`, and change-close, which every archive passes first, now warns and names the remedy.
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
    - openspec/specs/keel-openspec-surface-overlay/spec.md
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
    - M2: the ADDED requirement is appended to `keel-openspec-surface-overlay`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:28d57179b888674b93dc8ced9f6eabeaabe0716704ba071e7bcce09e58ed1003 (keel 5.147.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.147.0 → 5.148.0; with the "An archive keeps the evidence a change tracked" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-openspec-surface-overlay`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
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

- E1: Archiving a change whose own ignore rules match tracked evidence keeps that evidence in version control, and the close warns before the move (#352, D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
