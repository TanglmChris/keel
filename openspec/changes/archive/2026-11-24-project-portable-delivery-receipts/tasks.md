## 1. Add a portable delivery observation

- [x] 1.1 Read delivery evidence through the stable todo query
  - Covers:
    - D1
    - D2
    - keel-portable-task-execution / Project delivery evidence in the portable task query
  - Touch:
    - src/core/chat/cli.js
    - src/core/codex-host.js
    - scripts/test_codex_host.js
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: Query real todo records through the public CLI before successful delivery, after the actual tick delivers and after an ambiguous native response. Check no model call, filesystem mutation or change to chat closure. Verify a role without captured receipts reports unobserved and an invalid registry reports unknown. Fails with: `portable query needs an unobserved delivery state`
    - M2 (regression): Run the managed-host suite, chat-records and bilingual CLI documentation checks.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5e019acf9cd060c2f9c526dafe5943923ebdfc403b2237525b33daf09403dac9 (keel 5.231.5)
    - M1: The public todo query distinguishes unobserved, acknowledged, and unknown. The same query leaves the task open and retains its ID across tick, no receipt and ambiguous delivery.
    - M1.red: `node --test --test-name-pattern="managed CLI lifecycle" scripts/test_codex_host.js` exited 1 with `portable query needs an unobserved delivery state`: the original JSON had no delivery member.
    - M1.green: `node --test scripts/test_codex_host.js` passed all 17 tests. Real todo queries check unchanged native request count and registry bytes in all cases, including pending claim and unreadable registry.
    - M2: Managed host suite passed 17 tests. `python3 scripts/validate_plugin.py --scenario chat-records --scenario docs-zh-match-english --scenario readme-states-the-cli` passed all 3, including unchanged chat state and cursors and non-todo shape.
    - Review:
      - Status: pass
      - Acceptance check: M1 observes real tick delivery and the native transport ambiguity through the same public query. The receipt projection does not mark chat or task completion.
      - Scope check: Five Touch files plus change artifacts. Local read returns an observation; no new runtime invocation, store, scheduling, approval, or permission path.
      - Findings: Resolved here: M1 proves portable delivery reads for confirmed, ambiguous, and unobserved outcomes. Durable owner: https://github.com/TanglmChris/keel/issues/544 for cross-harness writer release and automatic continuation.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Upper client uses the same task query and observes known, unknown and missing delivery evidence (D1, D2). Covered by: 1.1
- E2: Real two-host dispatch, writer release, recovery and portable result verification. Durable owner: https://github.com/TanglmChris/keel/issues/544
