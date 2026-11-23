## 1. Measure current dispatch and continuity

- [x] 1.1 Record host and Keel readiness
  - Mode: diagnose-only
  - Covers:
    - D1
    - D2
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - Reason: This is a read-only capability and dependency inventory. Existing host state machines are exercised through their stand-in scenarios and no implementation behavior is changed.
    - M1: Check installed host CLI surfaces, Keel capability projections for four targets, the actual Codex and Claude tick implementations and published host evidence. Run the Codex host and Claude same-harness shift validation scenarios. Cite concrete gaps for native queue equivalence, previously submitted side-effects, permission and budget, recoverable leases, and optional OpenSpec coupling.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4571960a615d4b49435cfd455dcc047df0ce478c4bb943041aa6c0f0fd2c2c7c (keel 5.231.4)
    - M1: artifact openspec/changes/cross-harness-readiness-baseline/evidence/baseline.md sha256:570a52eccaa7a8423b7a3d8b455ecedb8b15e977c09a11c3b95b07d627952781
    - Review:
      - Status: pass
      - Acceptance check: Observed native CLI surfaces and four projections, checked the real Keel routes and published host evidence, and ran codex-managed-host plus shift-cli-self-shift (2 passed). The report explicitly distinguishes stand-in results from real-host behavior.
      - Scope check: Only the selected change record and its evidence were written. The validation used disposable fixture repositories and stand-in host processes.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/544 — stable task/execution identities, effect reconciliation and fencing, permission and resource enforcement, real two-host recovery tests, and optional OpenSpec migration.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Inspect published, locally observed, and tested host surfaces (D1). Covered by: 1.1
- E2: Explain gaps around usage exhaustion and workflow portability (D2). Covered by: 1.1
