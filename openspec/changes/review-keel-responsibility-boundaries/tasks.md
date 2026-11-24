## 1. Current architecture and check on the proven duplication

- [x] 1.1 Audit current responsibility boundaries
  - Mode: diagnose-only
  - Covers:
    - D1
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - Reason: the deliverable is a reviewed technical inventory of the existing system.
    - M1: Trace the seven issue observations against named code paths and update their dispositions, including the independent push-lock branch, shift note archive and reused Git observations. Produce a responsibility map and an ordered set of scoped changes or decisions.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1dc97bd0cc5fd6fd51d282745655fe640a44d4755781ff2bcbb95e37f3fc891b (keel 5.231.5)
    - M1: artifact openspec/changes/review-keel-responsibility-boundaries/evidence/responsibility-review.md sha256:1f015065af93652b67856b61cb059f1b740ebd00e9a97143039a7694bfe569b4
    - Review:
      - Status: pass
      - Acceptance check: The report names the producing modules, reviews all seven original observations at the current baseline, and distinguishes duplicate data collection from distinct authorization and output semantics.
      - Scope check: Only the change record and historical report were written in the diagnostic task.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/544 — cross-harness execution evidence. Discard reason: the current lock stores, archive boundary, authorization forms and declaration readers serve demonstrably distinct uses; broad consolidation is unnecessary.
    - Blocker: none
    - Reauthorizations: none

- [ ] 1.2 Reuse Git worktree discovery for branch filtering
  - Covers:
    - D2
  - Touch:
    - src/core/worktrees.js
    - src/core/branches.js
  - Verify:
    - Strategy: equivalence
    - Base: ac0da21a
    - Fields: checked-out branch exclusion, merged branches, authorized prune, worktree overview and sync status
    - M1: Run the public validation scenarios worktree-overview, branches-lists-merged, branches-prune-under-authorization and sync-status-lists-local-only on the base and result. Confirm the selection, exclusions, branch authorization and Git 2.34 fallback via their real Git fixtures.
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Current responsibility map, reviewed overlap and prioritized dispositions (D1). Covered by: 1.1
- E2: One scanner for worktree observations without changing results (D2). Covered by: 1.2
- E3: Unified execution receipts and coordination across hosts. Durable owner: https://github.com/TanglmChris/keel/issues/544
