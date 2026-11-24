## 1. Align the reader path with shipped behavior

- [x] 1.1 Explain task evidence, product direction and receive boundaries
  - Covers:
    - D1
    - D2
  - Touch:
    - README.md
    - README.zh-CN.md
    - AGENTS.md
    - assets/bootstrap/AGENTS.md
    - docs/host-contract.md
  - Verify:
    - Strategy: evidence-first
    - Reason: This task changes documentation and generated prose; observe actual CLI and manifests as the source of truth.
    - M1: Cold-read both homepages to answer the four #564 questions from the text and linked sections. Check the published task/delivery states against public CLI fixtures, and timing of Claude and Codex notices and idle dispatch against shipped manifests and receiving tests.
    - M2: Check generated bootstrap wording by running the bootstrap and protocol scenarios, and verify English and Chinese docs and CLI command coverage.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b2753f955c0ae92216e9e27f61d52fa135f612c1350fb2c6759656d5b6c3d69f (keel 5.231.7)
    - M1: Starting from either README, the cold read finds the original todo ID and chat show JSON, distinguishes receipt acknowledgement from verification, names configured drain/tick or the opt-in watcher for idle Codex, and identifies automated cross-harness continuation and risk-based workflow selection as work under #544. Public chat-records, codex-managed-host and codex-receiving scenarios passed against the source manifests.
    - M2: delegation-resident-text, session-start-source-repo-protocol, source-repo-bootstrap-skip, readme-states-the-cli, readme-zh-matches-english and docs-zh-match-english passed. The generated bootstrap source is 1689 bytes. Default sandbox could not execute fresh temporary fixtures; rerunning in the same isolated test fixtures with process execution permitted passed all eight scenarios.
    - Review:
      - Status: pass
      - Acceptance check: Both README introductions answer the four acceptance questions from #564. Delivery descriptions match existing public fixtures and Claude/Codex native manifest contents.
      - Scope check: Five declared prose files and the change records. No hook registrations or behavior were edited.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/544 for automatic continuation and risk-based execution.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "OpenSpec execution discipline for AI coding agents" — the two README introductions. Updated by: 1.1
- I2: "on Claude only, the chat notices" — repository protocol. Updated by: 1.1
- I3: "Codex, which cannot wake on its own, is woken by `keel chat wake add`" — team communication sections in both READMEs. Updated by: 1.1

## Expectation Coverage

- E1: A reader of either homepage can discover commands, read evidence and identify the actual receive mechanism (D1, D2). Covered by: 1.1
- E2: Implementing and validating the cross-harness product goal. Durable owner: https://github.com/TanglmChris/keel/issues/544
