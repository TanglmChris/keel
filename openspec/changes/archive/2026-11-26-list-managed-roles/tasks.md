## 1. Read-only managed inventory

- [x] 1.1 List recorded managed roles by repository
  - Covers:
    - D1
    - D2
    - keel-codex-host-team / Read-only managed role inventory
  - Touch:
    - src/core/codex-host.js
    - bin/keel.js
    - scripts/test_codex_host.js
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: Exercise the public list in an empty and mixed repository, including unbound group members, effective park, malformed registry and mismatched binding. Check stable identities, no RPC and unchanged mailbox bytes on repeat.
    - M2 (regression): Run managed host and onboarding tests plus bilingual documentation checks.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e007d7d3b7f20971985c6d0137c1276c429209620de2a9885665b7a80e805a68 (keel 5.231.11)
    - M1: Public list returned an empty array in a new Git repository without creating a mailbox. With pending mail it listed only registered roles in role order, including parked and invalid registrations. Repeating it left the filesystem snapshot identical and the socket server counted zero connections.
    - M1.red: The public command exited 1 with the previous host usage string at the empty-repository assertion.
    - M1.green: The same command passed after adding the offline listing, including broken JSON, pending creation, worktree mismatch and a parked registration.
    - M2: All 39 managed host and onboarding tests passed. The bilingual docs scenario and strict OpenSpec validation passed.
    - Review:
      - Status: pass
      - Acceptance check: The test compares identities, pending work, stored receipts and actual socket connections across two public invocations.
      - Scope check: Only the five declared files changed outside the OpenSpec record. Delivery and recovery paths are unmodified.
      - Findings: Resolved here: M1 covers the missing query. Durable owner: https://github.com/TanglmChris/kaiwu-ip/issues/577 for consumer adoption.
    - Blocker: none
    - Reauthorizations: none

## Invalidates
- None.

## Expectation Coverage
- E1: Local operators can enumerate the actual registry without delivering work (D1, D2). Covered by: 1.1
- E2: Consumer migration. Durable owner: https://github.com/TanglmChris/kaiwu-ip/issues/577
