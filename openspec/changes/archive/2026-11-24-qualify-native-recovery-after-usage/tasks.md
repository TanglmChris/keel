## 1. Measure the paired native checkpoint

- [x] 1.1 Record usage failure after a local effect and serial continuation through another native runtime
  - Covers:
    - D1
  - Mode: diagnose-only
  - Touch: none
  - Verify:
    - Strategy: evidence-first
    - Reason: The deliverable is a measurement of two native runtimes through disposable local providers, with no Keel product behavior change.
    - M1: Run the isolated native fixture and verify the correlated usage failure, source process exit, stable original effect and distinct target tool receipt and file effect.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f62bfdab93235b118ca0fc0b90b74c34a1c9930a96cf97bd1597b3fb93c326ba (keel 5.231.5)
    - M1: artifact openspec/changes/qualify-native-recovery-after-usage/evidence/runs.txt sha256:ab98a4b9dedce783a19e6a2fffeeebda7d0652ba426216659e2f4aca33bde57c
    - Review:
      - Status: pass
      - Acceptance check: Native Codex returned usageLimitExceeded for the exact turn after the tool receipt. Its process exited before native Claude ran. Claude validated one original marker line and returned a tool receipt for the independent continuation artifact.
      - Scope check: Evidence files only. Both profiles, credentials, providers and worktree were disposable and isolated. No product or production state was changed.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/544 for live writer fencing, tick authorization and unresolved side effects.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: A stopped source leaves its effect available to the target without replay (D1). Covered by: 1.1
- E2: Runtime dispatch, writer fencing and recovery in live environments. Durable owner: https://github.com/TanglmChris/keel/issues/544
