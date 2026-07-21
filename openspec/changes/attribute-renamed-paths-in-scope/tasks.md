<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Attribute renamed paths in the scope check

- [ ] 1.1 Split a porcelain rename entry into both endpoints in gitPaths and lock it with a scenario
  - Covers:
    - D1 split a rename entry into both Touch endpoints
    - keel-core-gates / Dirty-worktree attribution is conservative / A rename within Touch attributes to both endpoints
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: keel gate task-complete with a valid base, on a git mv rename whose old and new paths are both in Touch, returns pass and reports no outside-touch problem; a new validator scenario locks this through the public gate interface
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Expectation Coverage

<!-- change-close requires this section. -->
- E1: A git mv rename whose old and new paths are both in Touch attributes to both endpoints and produces no false outside-touch scope failure. Covered by: 1.1
