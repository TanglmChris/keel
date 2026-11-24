## 1. Observe the durable delivery's native outcome

- [x] 1.1 Read exact native outcome and terminal inventory as separate observations
  - Covers:
    - D1
    - D2
    - D3
    - keel-portable-task-execution / Observe the original managed Codex turn and terminal inventory
  - Touch:
    - src/core/codex-host.js
    - scripts/test_codex_host.js
    - bin/keel.js
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: Use the real Keel CLI and a stand-in Unix app-server to check an original turn after handover, typed usage vs ordinary failure, missing identity and turn, associated terminal inventory and partial/unavailable endpoint evidence. Check that the offline query emits no requests and the native query issues no load, resume, start, terminal mutation or registry write. Fails with: `native receipt observation should succeed`
    - M2 (regression): Run managed-host and Codex registration/migration behavior suites and bilingual docs checks.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8c91cef2efc018b768ba5d18acc55b77dbe42f102a14f8782bc742bd55afcd11 (keel 5.231.7)
    - M1: artifact openspec/changes/observe-managed-codex-delivery/evidence/native.txt sha256:7cd16a2b601b11eec2dbf3ff5ef064e0827535eb3daf85cf060c297e47a5dce4
    - M1.red: The public managed CLI lifecycle test failed with `native receipt observation should succeed` because the former CLI refused `--observe`.
    - M1.green: The same CLI scenario passed all exact-turn cases using the stand-in transport. `python3 -u evidence/native_probe.py <repository>` against real Codex 0.171.0 observed the acknowledged original turn with typed exhaustion while its tool was still listed. The same turn remained exhausted after its terminal exited. Stopping the test endpoint yielded unknown observations and retained the exact receipt. The loopback provider received two requests total.
    - M2: `node --test scripts/test_codex_host.js scripts/test_codex_onboarding.js` passed all 33 tests, and the bilingual CLI, README and navigation checks passed all 3.
    - Review:
      - Status: pass
      - Acceptance check: The direct CLI verifies use of the original thread ID after handover, exact turn matching, ordinary 429 classification and readable native inventory. The public native probe distinguishes turn and tool states from a real host and keeps the receipt through an unavailable endpoint.
      - Scope check: Source, the existing test, the two runbooks and change evidence only. The default read and task JSON are unchanged. Request assertions prove no resume, start, dispatch or registry changes.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/544 for enforcement of released writer ownership, effect reconciliation and automatic scheduling.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Inspect an observed native turn and terminal inventory without dispatching or certifying safety (D1, D2, D3). Covered by: 1.1
- E2: Across-host work ownership, rate/budget policy, writer fence and effect reconciliation. Durable owner: https://github.com/TanglmChris/keel/issues/544
