# #541 isolated native diagnosis — 2026-11-17

## Scope and result

Task 1.1 is diagnosis only. No Keel product file, Kaiwu role registration,
production thread, existing daemon lifecycle, global reviewer setting, or
native writer protection was changed. The fixture owns a temporary Git repo
and role worktree at `/tmp/keel541-owned-TWsQQi/role`.

Installed runtimes: App stdio 0.165.0-alpha.1.2; managed Unix daemon 0.167.2.
Both experimental generated schemas expose native queue/settings/reviewer
methods. Experimental initialization is required. Official lifecycle reference:
https://learn.chatgpt.com/docs/app-server . Installed behavior below is the
evidence; schema presence alone is not a runtime guarantee.

## Observations

1. `idle-unload.json`: native per-thread `thread_unload_delay_secs:0` followed
   by unsubscribe yielded notLoaded after 2 seconds. Default control remained
   idle. This does not unload a foreign App subscriber or bypass its writer.
2. `busy-queue.json` and `history-policy-probe.json`: App busy turn
   `01a1e872-d704-7dc0-8cc4-18c2bf68f239` completed at 1794901251; queued
   turn `01a1e873-9595-7f31-a35c-3044c6c7f602` started at 1794901251 and
   completed at 1794901254 with BACKGROUND_QUEUE_DONE. Queue UUID maps to
   history userMessage.clientId. No backend turn/start was needed.
3. `idle-queue.json` and `idle-queue-app-result.json`: idle App also consumed
   the external native queue, completing turn
   `01a1e8d4-7398-7432-9cc1-8bb67c63c8cc` with IDLE_BACKGROUND_QUEUE_DONE.
   The external daemon briefly read an interrupted/incomplete turn snapshot
   before the App completed. Do not use a foreign snapshot as final outcome
   or as permission to re-deliver.
4. `queue-duplicate.json`: same clientUserMessageId on two queue/add calls
   created two entries; both duplicate-test entries were deleted. Native add
   is not idempotent. Claims must survive ambiguous RPC outcomes; queue and
   history reconciliation must precede retries.
5. `reverse-backend-start.json` and `reverse-app-result.json`: immediately
   after native backend turn/start on owned thread
   `01a1e87e-0822-7b00-8926-f5c5f6e2d305`, actual App input failed with
   `already has an active writer`. Later history showed the backend turn
   completed, with no accepted App turn for the refused input. This disproves
   bidirectional busy acceptance under the current two-writer connection.
6. `cwd-execution.json`: on the same owned thread, native resume with explicit
   cwd/runtimeWorkspaceRoots and explicit reviewer/on-request/workspace-write
   produced actual pwd outputs first in the temporary repo and then in the
   original role worktree. Both command exits were 0; original id/history
   stayed intact. No production role recovery was attempted. The two pwd
   turns were explicit diagnostic work, not hidden policy warm-up.
7. `app-after-native-policy.json`: subsequent real App turn retained owned
   cwd, auto_review, on-request and workspace-write. Native App added its
   usual per-thread visualization root; no network expansion was observed.
8. `blank-policy.json`: start/name alone had not persisted reviewer in the
   initial controls. Explicit native thread/settings/update persisted
   auto_review on a blank thread; a cold native resume without reviewer
   override returned auto_review with zero model turns.
9. `blank-first-app-policy.json`: that blank thread's very first actual App
   input completed with BLANK_THREAD_FIRST_APP_DONE, turn
   `01a1e8da-c637-7162-9670-0dcf502d7eda`; its turn context retained
   auto_review/on-request/workspace-write and the owned worktree. This is
   direct evidence against requiring a hidden initialization model turn.

## What this does not prove

- No test joined the App to the Unix daemon's execution endpoint. Shared
  history/native queue is not shared writer ownership.
- A producer-only backend plus App sole execution avoids competing writers,
  but does not establish execution after the App runtime fully exits.
- The fixture is projectless. Native same-id cwd recovery was proved, but
  production project/worktree attachment and all three Kaiwu core identities
  remain deployment acceptance, not already-tested production facts.
- Existing claims were not migrated or deleted; no production claim recovery
  procedure has been executed. A queue adapter still needs its own public
  CLI behavior tests and durable unknown-outcome reconciliation.

## Product and follow-up ownership

Original acceptance remains: direct frontend communication plus independently
persistent backend operation. App-only execution is a proposed trade-off, not
approved authority. The owner has been asked; no answer is inferred from time.
The native shared execution endpoint/lifecycle gap and subsequent implementation
are owned by https://github.com/TanglmChris/keel/issues/541 . Public diagnostic
checkpoint: https://github.com/TanglmChris/keel/issues/541#issuecomment-6944250292 .

No #541 product version was released. Publishing a version does not close a
failed acceptance. Official release, integration/rollback instructions and
active delivery to chief remain required; notification responsibility is recorded
at https://github.com/TanglmChris/keel/issues/541#issuecomment-6944100669 .
