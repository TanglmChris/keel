## 1. Receive the owned result

- [x] 1.1 Collect managed reviewer results by todo identity
  - Covers:
    - D1
    - D2
    - D3
    - keel-portable-task-execution / Collect an explicitly reported result from the owned execution
  - Touch:
    - src/core/codex-host.js
    - src/core/managed-task-result.js
    - src/core/chat/cli.js
    - bin/keel.js
    - scripts/test_codex_host.js
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: Dispatch a real chat todo through the public CLI, collect a designated native result by original ID, verify persistence, retry and open task after collection. Fails with: `owned result collection failed`
    - M2 (regression): Exercise stale ownership, unknown/mismatched results, protected chat data and legacy receipts. Run existing managed-host scenarios.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:36d2dccb88637c6d6751de54da10e6ea1ec07cd1d27e27a735dc57590de979aa (keel 5.231.10)
    - M1: A real isolated Codex 0.172.0 worker read a fixed Git blob, verified its mailbox was not writable and returned the SHA-256 in its final native message. The controller collected it on the original todo, left it open and read it after the endpoint exited. Two loopback provider calls, zero live inference. Reproducer in evidence/native.py.
    - M1.red: The public scenario failed with owned result collection failed when show did not accept --collect.
    - M1.green: The same public scenario passed. It tested the exact role, thread, turn, persisted text and a repeated collection with zero additional RPCs.
    - M1.red: pending
    - M1.green: pending
    - M2: 37 Node host/onboarding tests and bilingual documentation checks passed. Cases rejected a successor thread, pending handover, migrated generation, legacy or pending claim, wrong turn or task ID, commentary, tool output, unfinished turn and pending migration, preserving the registry bytes.
    - Review:
      - Status: pass
      - Acceptance check: The CLI exercise covers returned data and actual cold offline rereads. The native exercise verifies the worker itself cannot write the mailbox.
      - Scope check: Product edits confined to declared paths. The existing show command is read-only unless --collect is explicitly requested.
      - Findings: Resolved here: M1 confirms result collection within the current owned execution. Durable owner: https://github.com/TanglmChris/keel/issues/544 for portable fault recovery and policy rollout.
    - Blocker: none
    - Reauthorizations: The owner delegated the interface. During the red test the collector was placed on existing show as an explicit --collect flag to keep group names available. M1 and M2 were both run on that final interface; their assertions and write boundary are unchanged.
    - Reauthorizations: none

## Invalidates
- None.

## Expectation Coverage
- E1: Only an explicitly reported result from the current assignment can be received (D1, D2, D3). Covered by: 1.1
- E2: Automatic transfer and externally observable effects. Durable owner: https://github.com/TanglmChris/keel/issues/544
