## 1. Observe native outcomes with small pages

- [x] 1.1 Search bounded native turn metadata
  - Covers:
    - D1
    - D2
    - keel-portable-task-execution / Bound native turn observation independently of transcript size
  - Touch:
    - src/core/codex-host.js
    - scripts/test_codex_host.js
  - Verify:
    - Strategy: regression-first
    - M1: The exact original turn is found on the second page through the public CLI, with no turn items requested. A repeated cursor terminates the unsuccessful read and keeps the terminal inventory independent. Fails with: `receipt query must avoid full native transcript`
    - M2 (regression): Existing host suite and the real Codex 0.171.0 loopback observation fixture pass.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:828926ee43550eda1b79b2318ec2cfd3ff31bc4763e77d67fb7eb01b6b30c684 (keel 5.231.7)
    - M1: The public observation requests identity without full turns, reads the exact recorded turn on page 2 using notLoaded items, and stops on a repeated cursor with terminal inventory preserved.
    - M1.red: The existing CLI lifecycle test failed with `receipt query must avoid full native transcript` on the earlier includeTurns read.
    - M1.green: The same public CLI lifecycle passed with exactly two pages for the old turn and two calls before refusing the repeated cursor. Request assertions prove no transcript or item content was requested.
    - M2: Both host Node suites passed 33 tests. Replayed the archived native_probe.py with real Codex 0.171.0, observing resource exhaustion with present and later empty inventory, then unknown after endpoint stop. Separate native read after restart retained the typed failure with 0 items loaded.
    - Review:
      - Status: pass
      - Acceptance check: Two-page and repeating-cursor behavior is checked at the public CLI using the native transport boundary. The real host confirms typed usage failure and live terminal inventory are retained under lightweight paging.
      - Scope check: Only the native observation implementation, its fixture and selected change records are modified.
      - Findings: Resolved here: M1 proves receipt observation is independent of full native transcript size. Durable owner: https://github.com/TanglmChris/keel/issues/544 for writer fencing and recovery.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Resume can classify an older recorded turn independently of transcript size (D1, D2). Covered by: 1.1
- E2: Native observations remain separate from old-writer fencing and automatic recovery. Durable owner: https://github.com/TanglmChris/keel/issues/544
