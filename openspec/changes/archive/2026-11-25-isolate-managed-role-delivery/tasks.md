## 1. Isolate independent managed roles during dispatch

- [x] 1.1 Remove sequential waiting across roles in tick and drain
  - Covers:
    - D1
    - D2
    - keel-codex-host-team / Managed mailbox delivery is independent across roles
  - Touch:
    - src/core/codex-host.js
    - src/core/tick.js
    - bin/keel.js
    - scripts/test_codex_host.js
  - Verify:
    - Strategy: regression-first
    - M1: Run public tick and drain in two owned worktrees with a confirmed held native turn acknowledgement on role A. Require role B's first native turn while A is still held, then release an ambiguous A reply. Assert A's second record starts no turn, a later dispatch does not replay either released claim, and reported roles keep their order. Fails with: `healthy delivery waited for slow acknowledgement`
    - M2 (regression): Run existing managed-host, onboarding and tick regression suites.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a4dc3a069f00a3f89a8bebed56a6164c1f2b42fb1416f9c57786ab8377cdeab8 (keel 5.231.8)
    - M1: In two disposable Git worktrees on separate Unix sockets, both CLI paths delivered role B while role A still withheld its native acknowledgement. The unknown A claim blocked its second record, the successful B claim deduplicated on another dispatch, and role result order was unchanged.
    - M1.red: `node --test --test-name-pattern="delivers an independent role" scripts/test_codex_host.js` failed for tick and drain with `healthy delivery waited for slow acknowledgement`. A reply had to be released before B could begin.
    - M1.green: Both scenarios passed in the same suite using the public CLI. The hold must still be in effect when B arrives, independently of the report order. The full test duration per scenario was 628 ms and 658 ms on this local fixture.
    - M2: Managed-host and onboarding Node suites passed 35 tests. Eight additional tick CLI scenarios passed covering Claude retry, patrols, quota, issue checks, heartbeat, scheduler settings and lease renewal.
    - Review:
      - Status: pass
      - Acceptance check: M1 verifies request order at the Unix transport and checks persisted claim outcomes and second dispatch, not just final JSON. M2 exercises the existing non-Codex CLI behavior.
      - Scope check: Four Touch files and the selected change. No permission, lock, native identity, mailbox addressing or remote configuration change. Each role retains one current child and the old child timeout.
      - Findings: Resolved here: M1 proves one blocked role does not delay independent dispatch. Durable owner: https://github.com/TanglmChris/keel/issues/544 for cross-harness admission, writer fencing and reconciliation.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: A slow endpoint no longer delays another owned role's first dispatch, while preserving each role's safeguards (D1, D2). Covered by: 1.1
- E2: Cross-harness admission, writer fencing, and unresolved external effects. Durable owner: https://github.com/TanglmChris/keel/issues/544
