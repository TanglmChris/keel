## 1. Read-only identity and closure for chat-backed tasks

- [x] 1.1 Project the stable task ID and chat closure through the existing JSON reader
  - Covers:
    - D1
    - D2
    - keel-portable-task-execution / Query a chat-backed task by its stable identity
  - Touch:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - scripts/validation/chat.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: The public chat-records scenario asserts a stable todo identity and closure receipt across repeated queries, explicit done and completion reply, including after group archive. Check ordinary message and closure JSON compatibility and check snapshots of logs and cursors around queries. Fails with: `task view missing for open todo`
    - M2 (regression): Run chat-core, chat-direct-participants-json and docs-zh-match-english. Review both runbooks against the exact CLI output and chat closure semantics.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:816cd0020848ad72ff38bdcd4fa469188c17c276b267fe07a3baa3ecc773c5f4 (keel 5.231.4)
    - M1: chat-records passed against the public CLI. The same todo ID projects open/null then closed with a resolvable done record. Explicit done uses the exact returned receipt ID. Archive and repeated queries retain the receipt, ordinary message and receipt JSON retain their former shape, and log/cursor snapshots agree.
    - M1.red: Before the implementation, python3 scripts/validate_plugin.py --scenario chat-records exited 1 with task view missing for open todo.
    - M1.green: After implementation, the same public CLI scenario passed including archive reads and cursor/log snapshots.
    - M2: chat-core, chat-direct-participants-json and docs-zh-match-english passed. The English and Chinese CLI guides name the same existing command and distinguish chat closure from verification evidence.
    - Review:
      - Status: pass
      - Acceptance check: The CLI queries persisted, real chat records across independent processes, and distinguishes an open task, generated and explicit closure, and ordinary chat. No published execution outcome is inferred from the receipt.
      - Scope check: Only the declared store, JSON reader, existing chat validation and two guides changed, plus change records. The native diagnostic ran against a separate disposable workspace, isolated HOME/config and loopback provider.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/544 — writer fencing, correlated native execution outcomes and account-level exhaustion classification must precede automatic continuation. Claude background idle/blocked and persisted rate_limit established only for the isolated generic 429 probe.
    - Blocker: none
    - Reauthorizations: Before test or product writes, clarified the intended group archival scope and re-recorded the capsule. No prior test evidence existed.

## Invalidates

- None.

## Expectation Coverage

- E1: Expose a stable todo identity and actual closure record through the same read (D1, D2). Covered by: 1.1
- E2: Portable execution receipts, task authority, host-neutral scheduling, safe handover and configurable workflow policy. Durable owner: https://github.com/TanglmChris/keel/issues/544
