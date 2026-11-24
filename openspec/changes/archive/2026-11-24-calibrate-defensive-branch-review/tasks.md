## 1. Calibrate the review on actual behavior

- [x] 1.1 Replay four selected Keel workload boundaries
  - Mode: diagnose-only
  - Covers:
    - D1
    - D2
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - Reason: this task measures and classifies already existing behaviors and defines the follow-up sampling protocol.
    - M1: Run the public pure-filter, guard-scope, runner refusal, Git compatibility and native ACL migration scenarios. Review both deletion and preservation candidates against expected behavior. Record provenance, timing and limitations.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0db83bf525ffa4cc7ef77529ae9daa5aaaf8aa3046f997b664250695e4a9f718 (keel 5.231.5)
    - M1: artifact openspec/changes/calibrate-defensive-branch-review/evidence/runs.txt sha256:1ce3e793230dbadfb0e8a59f236dd8a5510a579bbee8f573f1c6c6c502557234
    - Review:
      - Status: pass
      - Acceptance check: Five scenario selectors and six executable controls cover the four workload families. Actual outcomes and preservation conditions appear in calibration.md and runs.txt. No model-specific conclusion is claimed.
      - Scope check: Only change evidence was written. Tests used public Keel code and temporary inputs. No paid model or skill change occurred.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/533 — compare labelled model runs before changing common guidance or deciding on model attribution.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Calibrate useful and excessive defenses with observed behavior (D1). Covered by: 1.1
- E2: Measure a controlled model comparison and evaluate a skill change with representative labelled patches. Durable owner: https://github.com/TanglmChris/keel/issues/533
