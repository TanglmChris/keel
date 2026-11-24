## 1. Record and expose original delivery receipts

- [x] 1.1 Expose the managed delivery receipt without host I/O
  - Covers:
    - D1
    - D2
    - D3
    - keel-portable-task-execution / Inspect a durable managed Codex delivery receipt
  - Touch:
    - src/core/codex-host.js
    - bin/keel.js
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
    - scripts/test_codex_host.js
  - Verify:
    - Strategy: vertical-tdd
    - M1: Public managed CLI lifecycle test asserts persisted original thread after real handover, unknown with original thread after ambiguous delivery, unrecorded when absent and nullable original thread for legacy delivered claims. Assert no app-server requests on queries and no registry mutation. Fails with: `delivery receipt must preserve its original thread`
    - M2 (regression): Run scripts/test_codex_host.js and scripts/test_codex_onboarding.js and verify documentation names the offline query and evidence boundaries.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d12e3656b4ca1712e58831090960624ec0727b7315cd2cc08abcbe31253d8156 (keel 5.231.5)
    - M1: Public CLI lifecycle proves the original thread and native turn survive handover. Unknown and absent receipts remain distinct, legacy thread stays null, and lookups leave RPC and registry unchanged.
    - M1.red: Regression assertion `delivery receipt must preserve its original thread` failed on the original CLI, which returned successor thread2 rather than the retained thread1 receipt.
    - M1.green: The managed-host and onboarding Node suites exited 0 with 33 passing tests combined. Lifecycle assertions inspect the original delivery after handover, an ambiguous delivery, an absent record, a legacy record and the unchanged RPC/registry.
    - M2: `node --test scripts/test_codex_onboarding.js` exited 0 with 16 passing tests via isolated Unix sockets. Docs, English README CLI and Chinese README checks passed (3 scenarios).
    - Review:
      - Status: pass
      - Acceptance check: M1 exercises the real Keel CLI with fake native RPC only at its transport boundary. Claims are read from Keel-owned records and preserve observable native provenance.
      - Scope check: Changes stay in the five Touch files and this change stream. Query does not write or initiate RPC. Existing delivery/deduplication outcomes and the legacy claim format remain readable.
      - Findings: Resolved here: M1 establishes the original thread lookup after handover. Durable owner: https://github.com/TanglmChris/keel/issues/544 for shared attempt generation, runtime reconciliation and writer fencing.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Claims retain original provenance and remain inspectable after handover and failure (D1 and D2). Covered by: 1.1
- E2: Automatic recovery and old writer fencing. Durable owner: https://github.com/TanglmChris/keel/issues/544
