# Tasks

## 1. Recent issues

- [x] 1.1 An idle `keel context` carries the issues the branch's commits reference, and the projection prints them
  - Covers:
    - keel-stateless-continuity / An idle result points at the issues the branch was working on / An idle branch names its recent issues
    - keel-stateless-continuity / An idle result points at the issues the branch was working on / Nothing to point at adds nothing
    - D1
    - D2
    - D3
    - F1
    - F2
    - F3
  - Read:
    - src/core/worktrees.js
    - src/core/context.js
    - plugins/keel/scripts/session-start.js
  - Touch:
    - src/core/worktrees.js
    - src/core/context.js
    - plugins/keel/scripts/session-start.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario idle-recent-issues` builds a repository with `openspec/` and a worktree whose branch commits beyond `main` mention `#162`, `#182`, then `#162`, and requires `keel context --json` there to report `idle` with `recent.issues` `[162, 182]` and the same reasons as without them, the real SessionStart hook to print `recently referenced: #162, #182`; and on `main` itself, no `recent` field and no such line. Fails with: `idle-recent-issues:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3e9b30db5f5f2a139ee7084f6daeb1b22dd8020ae1866bc61cf7350593925151
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario idle-recent-issues` reports `idle-recent-issues scenario passed.`
    - M1.red: fail. Before the change the scenario reported `idle-recent-issues: recent is None, not issues [162, 182].`, carrying the declared signature `idle-recent-issues:`.
    - M1.green: pass. With `branchIssues` shared from `src/core/worktrees.js`, `recent` set on idle results in `resolveContext`, and the hook's line, the worktree reports `recent.issues` `[162, 182]` with reasons identical to `main`'s, the compaction note prints `recently referenced: #162, #182`, and `main` has neither. `worktree-overview` still passes on the shared reader.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 257 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario commits real messages on a worktree branch and reads `keel context --json` and the shipped hook's compaction output there and on `main`.
      - Scope check: `git status --short` lists `src/core/worktrees.js`, `src/core/context.js`, the session-start hook, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Resolved here: M1. A remote's default branch resolves to `origin/main` while the checkout's branch is `main`, which would have listed unpushed commits on the default branch; the comparison now strips the remote prefix.
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
    - openspec/specs/keel-stateless-continuity/spec.md
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
    - M2: the ADDED requirement is appended to `openspec/specs/keel-stateless-continuity/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:478d444566bce37eeb97772c90ed1ed2c08514d30f9e5d7ea87683f4cb738f53
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.111.0 on top of `main` at 5.110.0 (#284). With the 5.111.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-stateless-continuity/spec.md`; `published-specs-validate-strictly` reports `34 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published spec carries the requirement with both scenarios, and the changelog names the issue and its origin in #241.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.111.0 reports `validation --all passed: baseline plus 257 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: An idle session sees, from Git alone, which issues its branch was last working on, without anything being selected (D1–D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
