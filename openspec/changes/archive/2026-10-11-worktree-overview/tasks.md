# Tasks

## 1. The overview

- [x] 1.1 `keel worktrees` lists every worktree's state, with issue times only from a passed file
  - Covers:
    - keel-worktree-overview / One read-only command lists every worktree's state / Two worktrees are listed with their state
    - keel-worktree-overview / One read-only command lists every worktree's state / A missing worktree is listed as missing
    - keel-worktree-overview / Issue update times come only from what the caller passes / Passed issue times are shown
    - keel-worktree-overview / Issue update times come only from what the caller passes / An unreadable issues file is refused
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
  - Read:
    - src/core/shift.js
    - src/core/chat/store.js
    - src/core/chat/notice.js
    - bin/keel.js
  - Touch:
    - src/core/worktrees.js
    - bin/keel.js
    - scripts/validate_plugin.py
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario worktree-overview` builds a repository with a bare remote, worktree `a` bound to role `pm` on branch `feature` one commit ahead of its upstream with a commit mentioning `#12`, worktree `b` on a detached head with one uncommitted file, and a third worktree whose directory is deleted; requires `keel worktrees --json` to report each as D2 describes, the text output to name the default branch and say the counts are as of the last fetch, `--issues` with a file holding issue 12's `updatedAt` to show it, a missing and a non-JSON `--issues` file each to exit 1 naming the file, and the chat store's files to be byte-identical before and after. Fails with: `worktree-overview:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c9b9ef88cf7c55171505ffdcb5b5e50b26fcafa3155b153bbe807cb373b55836
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. Re-run by this session in its own checkout: `node scripts/run_python.js scripts/validate_plugin.py --scenario worktree-overview` reports `worktree-overview: scenario passed`.
    - M1.red: fail. Re-run by this session with `bin/keel.js` restored to its committed version and `src/core/worktrees.js` removed: `worktree-overview: --json failed: keel: repo path was provided more than once`, carrying the declared signature `worktree-overview:`. Codex's own red, the same line, is in its worktree's `runs/1.1/M1.red.log`.
    - M1.green: pass. With codex's `src/core/worktrees.js`, its dispatch and help line, and the README section, the scenario passes here; `assertion-shape-count` reports 80 sites and `the-tarball-is-the-repository` 72 packed files, all tracked.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario builds four worktrees with a local bare remote and drives the real CLI: per-worktree fields as D2 lists them, the missing worktree, the default branch and fetch wording in text, issue times from a passed file and null when absent, refused unreadable and malformed `--issues` files with empty stdout, and byte-identical chat store and repository files before and after.
      - Scope check: `git status --short` lists the four Touch paths and this change's own directory. Codex's worktree changed the same four plus its own `runs/`, which stays there.
      - Findings: Discard reason: codex's single `npm test` run in its sandbox failed 32 scenarios, each traced in its report to the sandbox (local port binding and the npm cache refused, temporary fixtures nested inside the checkout); this checkout's own C1 run is the regression evidence, not codex's. Discard reason: `#<n>` is read from every commit subject and body on the branch, so a mention of something other than an issue is listed too; the list is a pointer for the coordinator, not a selection.

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
    - openspec/specs/keel-worktree-overview/spec.md
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
    - M2: the ADDED requirements become `openspec/specs/keel-worktree-overview/spec.md` with a Purpose, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:96c73be47b22cb613caa9bcdb90d89a83501b70c94c341edcbd51d3fc903fdca
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. After merging `main` (5.101.0, #269; the one conflict was both changes registering a scenario at the same line, and both were kept), `node scripts/bump_version.js minor` moved every marker to 5.102.0. With the 5.102.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirements became `openspec/specs/keel-worktree-overview/spec.md` with a Purpose; `published-specs-validate-strictly` reports `33 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the new capability is published with both requirements and their scenarios, and the changelog names the issue, the behavior, and the delegation.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after merging `main` and the bump to 5.102.0 reports `validation --all passed: baseline plus 242 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: A coordinator reads every worktree's state from one read-only command instead of assembling it by hand, with nothing fetched behind its back (D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
- E3: Running job counts against a declared budget (D6). Discard reason: the issue itself defers it; it needs a declared budget and per-session process attribution, neither of which exists yet.
