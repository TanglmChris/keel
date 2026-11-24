## 1. Replay an acceptance counterexample

- [x] 1.1 Run the pilot against two requirements
  - Mode: diagnose-only
  - Covers:
    - D1
    - D2
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - Reason: the experimental fixture is the recorded evidence for a review pilot rather than deployed behavior.
    - M1: Run the archived pilot to demonstrate the two-clock baseline, the first public difference on the legal three-clock trace, and classification of the same trace as excluded by the explicit two-clock limit. Exercise a correct reference implementation as a positive control and report elapsed probe time.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ff6fe086bf734d73e76b3c6b418526b0b5cd5ba55f2aaa82363fb48687783661 (keel 5.231.5)
    - M1: artifact openspec/changes/verify-acceptance-counterexample-pilot/evidence/result.txt sha256:8fe605b4b37f1ee5f1a4a1328637f2d31cfc21c9dfe2db0eeee75ba22fff5756
    - Review:
      - Status: pass
      - Acceptance check: Verified the same public trace under uncapped and capped requirements, observed the first incorrect transfer on the uncapped case, and checked a positive implementation. evidence/assessment.md explains the oracle, timing and limits.
      - Scope check: Only the selected record layer and its synthetic fixture changed. No production interface, workflow or skill text was modified.
      - Findings: Discard reason: one bounded fixture supports the existing semantic Review question and does not justify a new required gate; replay and disposition are archived.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Reproduce a green baseline and a legal counterexample with an independent oracle (D1). Covered by: 1.1
- E2: Distinguish an explicitly excluded trace and retain replay evidence (D2). Covered by: 1.1
