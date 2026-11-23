## 1. Create and use project-local worktrees

- [x] 1.1 Implement explicit Git worktree creation and document the Codex CLI workflow
  - Covers:
    - D1
    - D2
    - keel-worktree-overview / Create a project-associated linked worktree explicitly
  - Touch:
    - src/core/worktrees.js
    - bin/keel.js
    - scripts/validation/shift.py
    - scripts/validation/registry.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: Run the public worktree CLI through the project-local-worktree scenario using real Git, two repositories, both implicit and explicit base, repeated creation, role visibility, existing branch and dirty checkout conflicts, and non-forced cleanup. Verify no other repository or local edits changed.
    - M2 (regression): Run existing worktree-overview scenario and verify both runbooks use the returned checkout in Codex CLI and describe Git discovery and safe cleanup.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:85a85bd502dc3303cce250cf43ed08a2b978bc2a2e87906f1ee694b800dc8468 (keel 5.231.3)
    - M1: The registered project-local-worktree scenario exercises both real repositories, reports the exact linked path and commits, resolves roles per repo, rejects occupied paths and duplicate branches and verifies safe Git removal.
    - M1.red: The new public scenario failed with Unknown argument add before the command existed.
    - M1.green: python3 scripts/validate_plugin.py --scenario project-local-worktree passed after implementation and prechecking the occupied destination.
    - M2: python3 scripts/validate_plugin.py --scenario worktree-overview passed. The English and Chinese runbooks use the reported path with the -C option reported by Codex 0.171.0 and document ordinary Git cleanup.
    - Review:
      - Status: pass
      - Acceptance check: Real CLI and Git exercise behavior, including isolation from local edits, native branch collision and dirty cleanup refusal. The runbook composes the verified checkout with the native CLI working-directory flag.
      - Scope check: Only the CLI, existing Git worktree module, validation fixture and registry, and both runbooks changed relative to commit 969b4ae0, plus this change record.
      - Findings: Resolved here: M1 asserts no branch is created when a destination is already occupied. Git on this machine otherwise creates a new branch before it reports that conflict.
    - Blocker: none
    - Reauthorizations: Clarified the same occupied-path rejection reason after the real Git test showed branch creation precedes path validation. M1 assertions did not change. Retained its red and re-ran both green checks.

## Invalidates

- None.

## Expectation Coverage

- E1: Explicit project-associated checkout creation via Git (D1). Covered by: 1.1
- E2: Authentic role discovery, Codex launch and non-forced cleanup (D2). Covered by: 1.1
