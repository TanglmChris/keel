## Why

Downstream issue #531 measured a managed PM becoming notLoaded after its first completed turn. Keel then rejects both new result delivery and duplicate records, breaking the second round of a real team workflow.

## What Changes

- Return a verified recorded delivery claim before checking load state, without resuming for deduplication.
- For new work only, resume an identity-verified owned notLoaded thread on the same connection and revalidate its identity/state before delivery.
- Preserve operation locks, durable claims, waiting behavior, permissions and failure refusal; never create a replacement thread or adopt unrelated desktop chats.
- Prove a real two-role result round trip after the PM's first completed turn and unload.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-codex-host-team`: owned-thread recovery and idempotent delivery after unload.

## Impact

src/core/codex-host.js, the public CLI host scenario and bounded host documentation. Release together with the independently verified #528 dependency repair. #527 stays deferred.
