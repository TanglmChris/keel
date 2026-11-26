## 1. Preserve invalid delivery claims

- [x] 1.1 Refuse retries when the delivery key already exists without a usable receipt
  - Covers:
    - D1
    - D2
    - D3
    - keel-codex-host-team / Preserve invalid delivery claims
  - Touch:
    - src/core/codex-host.js
    - scripts/test_codex_host.js
  - Verify:
    - Strategy: regression-first
    - M1: Use public receipt, portable todo and deliver paths against null and false claims, malformed maps and a missing key. Compare original registration bytes and host requests. Verify the invalid cases cannot start a turn.
    - M2 (regression): Run all host and onboarding tests including successful first delivery and deduplication. Exercise a real isolated Codex host with the same record and thread.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:eb2aad8876505100489bae55d61a35751a79b15a744e779d30e7c73248a925ce (keel 5.231.12)
    - M1: Nine fixtures covered absent map/key, null/false/zero/empty values and invalid maps. Public status, portable chat show and refused retries preserved the exact bytes without a live socket.
    - M1.red: On 5.231.12 the null receipt was unrecorded instead of unknown. An isolated native app-server completed two distinct turns on the same thread and record after the null retry, with two loopback provider calls.
    - M1.green: All damaged-claim cases passed with the fixed CLI. Isolated native retries for null and false both refused without changing the bytes; the only provider call was for the initial, confirmed turn.
    - M2: All 40 managed host and onboarding tests passed. Restoring the original intact receipt in the temporary native fixture returned already-delivered and the exact first turn without another provider request.
    - Review:
      - Status: pass
      - Acceptance check: The same fixture A/B measured new native turns on the published baseline and verified both corrupt entries, original identity, registry bytes, and provider count on the fix.
      - Scope check: Product changes confined to managed receipt classification and dispatch plus its public regression test. The existing delivered path still verifies native identity before returning the original turn.
      - Findings: Resolved here: M1 and M2 cover the duplicate and the unaffected successful path.
    - Blocker: none
    - Reauthorizations: none

## Invalidates
- None.

## Expectation Coverage
- E1: An unusable existing claim never becomes permission to repeat work (D1, D2, D3). Covered by: 1.1
- E2: Downstream migration. Durable owner: https://github.com/TanglmChris/kaiwu-ip/issues/577
