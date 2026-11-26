## 1. Mixed-team tick dispatch

- [x] 1.1 Resume independent ended Claude sessions while Codex deliveries wait
  - Covers:
    - D1
    - D2
    - keel-codex-host-team / Independent Claude wake during managed delivery
  - Touch:
    - src/core/tick.js
    - scripts/test_codex_host.js
  - Verify:
    - Strategy: regression-first
    - M1: Through the public tick CLI, hold a managed acknowledgement, verify a separate ended Claude session receives its original resume and a second tick observes its persisted wake before releasing the first receipt. Require an unknown Codex claim and no repeated turn. Fails with: `Claude wake waited for Codex acknowledgement`
    - M2 (regression): Run the existing managed-host tests and tick retry scenario.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:536e53a8f800ab8ccdfca2b42437a7ddf71a7449f47f15f512156fe3687641bc (keel 5.231.9)
    - M1: Public tick resumed the eligible Claude session once, persisted its addressed record, and a second tick returned no Claude wake while the first managed turn was withheld. Releasing an incomplete acknowledgement left that managed claim unknown with one native turn.
    - M1.red: Before the scheduler change, the CLI fixture failed with Claude wake waited for Codex acknowledgement. The slow endpoint received its turn and no wake was recorded within the hold.
    - M1.green: The same Node test passed after the change, including the overlapping second tick and the recorded original session ID.
    - M1.red: pending
    - M1.green: pending
    - M2: All 36 managed-host and onboarding Node tests passed. The tick-retries-failed-wake public CLI scenario passed for both retry and removed-session cases.
    - Review:
      - Status: pass
      - Acceptance check: The regression observes the actual CLI wake command, durable record and managed endpoint. It checks the two host effects separately and the next tick before releasing the receipt.
      - Scope check: Only the scheduler and its public CLI scenario changed. Eligibility, ownership and both host commands retain their existing checks. Hand-over and patrol still follow wake processing.
      - Findings: Resolved here: M1 covers independent progress across host types. Durable owner: https://github.com/TanglmChris/keel/issues/544 for same-task continuation and constrained result submission.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Independent work can proceed across the two host wake paths. Covered by: 1.1
- E2: Automatic continuation of the same task, admission, result submission and external effect reconciliation. Durable owner: https://github.com/TanglmChris/keel/issues/544
