## 1. Owned endpoint migration

- [x] 1.1 Validate target before intent and verify real source unload before acquiring
  - Covers:
    - D1
    - D2
    - D3
    - keel-codex-host-team / Endpoint migration has a verified native handoff
  - Touch:
    - src/core/codex-onboarding.js
    - scripts/test_codex_onboarding.js
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: regression-first
    - M1: Use the public CLI with two native RPC boundary hosts. On the second history page omit only a new metadata field. Both inspect and apply must fail before intent or source unsubscribe and must never resume the target. Verify stale target ID and cwd at apply.
    - M2: Use the public CLI with delayed source unload; assert a read of the original source sees unload before a single target resume. Hold the writer indefinitely using an explicit short timeout; verify unknown releasing phase, retained registration, zero target resume and refusal on retry. A writer race after observed unload still refuses and stays unknown.
    - M3 (regression): Run node --test scripts/test_codex_host.js scripts/test_codex_onboarding.js. Review both operator runbooks against the phase ordering and timeout semantics.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a536b814419234b0334e3cddf525ec467592ee90fc0061674861e85274eb2c05 (keel 5.231.2)
    - M1: The public CLI rejects second-page environmentId loss at both inspection and apply, and rejects target ID/cwd drift before intent, unsubscribe or target resume.
    - M1.red: The focused node --test target cold preflight case failed at inspect exit status, which was 0 with the incomplete target view.
    - M1.green: The same focused test passed (1/1).
    - M2: After unsubscribe, the delayed source case observed two original-source reads before its only target resume. The held case reported unknown/releasing and sent no target resume. A writer race reported unknown/acquiring after one refusal. Registry equality and no normal retry were checked.
    - M2.red: Both focused node --test source unload tests failed: the former immediately hit active writer; the latter hit the same writer refusal instead of a bounded source unload timeout.
    - M2.green: Both cases passed in the full Codex lifecycle/onboarding run.
    - M3: node --test scripts/test_codex_host.js scripts/test_codex_onboarding.js: 33 passed, no failures or skips. Both runbooks describe preflight, source observation, explicit timeout, unknown and reconcile.
    - Review:
      - Status: pass
      - Acceptance check: The real CLI and registry were exercised against controllable native RPC boundaries. The two failure reproductions assert phase and side effects, and rehearsal preserves registry claims, native policy, and no automatic reacquisition.
      - Scope check: Relative to origin/main 614a34d0, edits are one CLI module, its two-host regression tests and the two declared runbooks plus this change record. Verification used disposable /tmp endpoints.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: Before test or product writes, strict OpenSpec validation required the existing writer scenario name. Restored that heading without changing its assertions, then re-recorded the task start fingerprint. No prior test evidence existed.

## Invalidates

- I1: "another subscriber retaining the writer causes a native refusal" and "其它订阅仍持有 writer 时由原生拒绝" — the English and Chinese operator guides need the source-observation deadline before any acquisition. Updated by: 1.1
- I2: "WHEN source unsubscribe does not release the native writer and target resume refuses" — current main host-team spec replaced by this change's delta after verified release. Updated by: 1.1

## Expectation Coverage

- E1: CLI detects the complete target history mismatch while the approved source is retained. Covered by: 1.1
- E2: CLI waits for confirmed source unload before requesting the native writer once. Covered by: 1.1
- E3: Unknown acquisition or release is inspectable and only explicitly reconciled, preserving the registry and claims. Covered by: 1.1
