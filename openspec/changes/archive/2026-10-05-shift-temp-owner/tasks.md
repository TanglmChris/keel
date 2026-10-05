# Tasks

## 1. Temporary worktrees by owner

- [x] 1.1 The readiness check counts only temporary worktrees of sessions started in this worktree
  - Covers:
    - keel-shift-change / The readiness check reports what would be lost or left running / Each kind of loose end is reported
    - keel-shift-change / The readiness check reports what would be lost or left running / Another session's temporary worktree does not block
    - D1
    - F1
    - F2
    - F3
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-change` places the loose temporary worktree at `claude-<uid>/<slug of verify>/<session>/scratchpad/` under the temporary directory and still requires `keel shift check` to name it as an item, and, once everything else is clean, adds a linked worktree at `claude-<uid>/-some-other-dir/<session>/scratchpad/` and requires `keel shift check` to exit 0 and name it in a note. Fails with: `shift-change:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:69562d3d419066fc5b2776afa81c4dcb1dd9218f0c627f45c2a9eebe4437ef8c
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-change` reports `shift-change scenario passed.`
    - M1.red: fail. Before the change the scenario reported `shift-change: another session's temporary worktree blocked the check: …- temporary-worktree: …/claude-501/-some-other-dir/keel-test-…/scratchpad/other-tmp-tree`, carrying the declared signature `shift-change:`.
    - M1.green: pass. With `temporaryWorktrees` split by the scratchpad slug, an own temporary worktree counted as an item and any other listed as a note, and the guides' `check` list updated, the scenario passes. Run read-only against rtl_ppa_flow's worktree (`keel shift check --repo …/rtl-workflow-dev-optimization-c6f6ee`), the three worktrees it reported now appear only as notes.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario builds both shapes of scratchpad path with real `git worktree add` and reads the check's exit code and output. The real report was re-run against the worktree it came from.
      - Scope check: `git status --short` lists the four Touch paths and this change's own directory.
      - Findings: Discard reason: a temporary worktree outside any Claude scratchpad, for example under Codex's or a script's `/tmp`, can no longer block a shift change. It is listed as a note, because Git records no creator (F3), and blocking on a guess is what this change removes.

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
    - M1: `node scripts/bump_version.js patch` moves every marker to 5.99.1, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.99.1 section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6bfe6709b22c28603ad544799bd6533447f2547db8348c07dbedde149c2b2e0d
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js patch` moved every marker to 5.99.1. With the 5.99.1 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its published copy, keeping its scenarios and adding one; `published-specs-validate-strictly` reports `31 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published requirement carries the scratchpad-owner rule and its scenario, and the changelog names the report and the rule.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump reports `validation --all passed: baseline plus 239 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "Linked worktrees under a temporary directory, other than this one and the main one." — the `check` list in `docs/shift-change.md` and its Chinese counterpart. Updated by: 1.1

## Expectation Coverage

- E1: One session's temporary worktree does not block another session's shift change (D1). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
