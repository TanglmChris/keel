## 1. Bound managed resume

- [x] 1.1 Exclude history on metadata-only managed resumes
  - Covers:
    - D1
    - D2
    - keel-codex-host-team / Bounded resume of managed Codex threads
  - Touch:
    - src/core/codex-host.js
    - scripts/test_codex_host.js
    - scripts/test_codex_onboarding.js
  - Verify:
    - Strategy: regression-first
    - M1: Run public managed delivery on an original thread whose default resume exceeds the Keel frame cap. Verify original identity and policy, duplicate receipt and no replacement turn. Fails with: `Codex response too large`
    - M2 (regression): Run the managed host and onboarding suites including recovery. Measure the native response with and without historical turns on an isolated Codex.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c35ca7ccdc52a0396962602f63288ea8604e33a06915527b61af7af3998bbc0d (keel 5.231.10)
    - M1: A cold native-resume fixture returns a historical frame larger than 16 MiB unless metadata is requested. Public deliver, repeat and recover passed on the original thread. Only one native turn was created, with the original reviewer and restored directory.
    - M1.red: The public CLI fixture failed with Codex response too large on the original managed resume.
    - M1.green: The same cold delivery, repeated receipt and recovery passed after both requests included excludeTurns.
    - M1.red: pending
    - M1.green: pending
    - M2: All 38 host and onboarding tests passed. Real Codex 0.172.0 with 22 synthetic turns returned 18,855,986 bytes in the original resume (22 turns) and 821,167 bytes with excludeTurns (zero turns). Both returned the same thread ID, worktree, approval policy and sandbox. The metadata payload includes a thread preview. The fixture used a loopback provider without live model calls.
    - Review:
      - Status: pass
      - Acceptance check: Native measurements isolate resume, and the public transport fixture tests the original protected frame cap, preserved identity, policy and deduplication.
      - Scope check: Two managed resume calls and their host/onboarding tests. Onboarding history verification remains independent.
      - Findings: Resolved here: M1 and M2. Deployment and pending production messages remain coordinated at https://github.com/TanglmChris/kaiwu-ip/issues/546.
    - Blocker: none
    - Reauthorizations: none

## Invalidates
- None.

## Expectation Coverage
- E1: Long history does not prevent identity-checked managed recovery or duplicate-safe dispatch (D1, D2). Covered by: 1.1
