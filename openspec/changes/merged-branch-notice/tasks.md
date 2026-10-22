# Tasks

## 1. Say what lags, and where to start

- [x] 1.1 Name a merged branch in `keel shift resume`
  - Covers:
    - keel-shift-change / Resume says when the worktree is on a branch already merged / A merged branch is named, an unmerged one is not
    - D1
  - Read:
    - openspec/changes/merged-branch-notice/design.md
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - scripts/validation/shift.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-resume-names-merged-branch`: with verify's worktree on `feat`, whose commit was pushed and fast-forwarded into the remote default branch with one more commit after it, the real `keel shift ready` then `keel shift resume` print a line naming `feat`, `already in origin/<default>`, and `1 commit behind`; after an unpushed commit on `feat`, another ready and resume print no line with `already in origin/<default>` for the branch. Fails with: `shift-resume-names-merged-branch:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group shift --jobs 4` passes, and so does `--scenario assertion-shape-count`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:342742316a734f248ecefde7c17c9665deae33ee58dacd4015d7186bd0d37fbc (keel 5.193.0)
    - M1: pass. `shift-resume-names-merged-branch scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `shift-resume-names-merged-branch: resume on merged branch feat does not say so: '# Shift note: verify…` (exit 1).
    - M1.green: pass. `mergedBranch` returns the branch, base, and count when HEAD is behind `origin/<default>` and an ancestor of it. Resume carries it as `merged_branch` and prints one line after the commit list (D1). It fetches nothing.
    - M2: pass. `validation --group shift passed: 55 scenarios.` (exit 0). `assertion-shape-count` passed at 74 sites.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel shift ready` and `resume`, a worktree on a branch fast-forwarded into the remote default branch, one commit behind it, is told so and where to start. The same branch with an unpushed commit is not.
      - Scope check: `git status --short` lists `src/core/shift.js`, the two validation files, and this change's directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

- [ ] 1.2 Name the branch, not a refresh, for a lagging protocol in Keel's source repository
  - Covers:
    - keel-native-runtime-projection / The session projection reports runtime version alignment / Keel's source repository names the branch, not a refresh
    - keel-native-runtime-projection / The session projection reports runtime version alignment / A lagging protocol names the protocol refresh
    - D2
  - Read:
    - openspec/changes/merged-branch-notice/design.md
    - plugins/keel/scripts/session-start.js
    - src/core/capabilities.js
  - Touch:
    - plugins/keel/scripts/session-start.js
    - scripts/validation/hosts.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario session-start-source-repo-protocol`: the shipping SessionStart hook, run with a plugin and CLI at 5.9.0 in a repository whose `package.json` is named `@christang/keel`, which has a `plugins/keel` directory, and whose `CLAUDE.md` stamps 5.2.0, states that the protocol block is the checked-out branch's version and the branch is behind, and names neither `keel --install` nor `Protocol: line`; the same hook in a repository without that `package.json` still names `keel --install --target claude`. Fails with: `session-start-source-repo-protocol:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group hosts --jobs 4` passes, `runtime-version-drift` among them, and so do `--scenario assertion-shape-count` and the `install` group with `--jobs 4`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract:
    - Blocker: none
    - Reauthorizations: none

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
    - openspec/specs/keel-shift-change/spec.md
    - openspec/specs/keel-native-runtime-projection/spec.md
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
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Tasks 1.1 and 1.2 prove the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the deltas are promoted into `keel-shift-change` and `keel-native-runtime-projection`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "The repository's protocol block is behind: refresh it with `keel --install --target …`, the command `keel context` names on its Protocol: line." — `plugins/keel/scripts/session-start.js`, for Keel's source repository only. Updated by: 1.2.
- I2: "the protocol refresh `keel --install --target <target>` … for the protocol" — `openspec/specs/keel-native-runtime-projection/spec.md`. Updated by: 2.1.

## Expectation Coverage

- E1: A resumed shift on a merged branch is told so and where to start (D1), and in Keel's source repository the startup hook names the lagging branch instead of a refresh (D2) (#446). Covered by: 1.1, 1.2
- E2: The release carries it. Covered by: 2.1
