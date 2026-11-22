## Why

Keel #546/#547 unblock Kaiwu's authorized dedicated native Codex deployment. Existing managed roles cannot change endpoints and already-created dedicated frontend roles cannot be registered without creating replacements.

## What Changes

- Add explicit, inspectable owned-role endpoint migration, preserving thread id, persistent history, role identity, delivery claims and approved policy.
- Add explicit registration of an authorized existing thread/role/worktree/endpoint tuple; preserve read-only review and never create a replacement or warm-up turn.
- Bind operations to a caller-provided authority reference and a reviewed immutable plan; retain uncertain transition outcomes rather than retrying native effects.
- Extend managed delivery/recovery to preserve the registered native policy. Publish CLI/runbook and private-fixture evidence, then notify Kaiwu.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-codex-host-team`: explicit endpoint migration and existing-thread registration.

## Impact

Managed CLI, native adapter, role registry, boundary tests and bilingual team docs. No new dependency. User explicitly admitted both implementation/release scopes by “继续” after the concrete #546/#547 request. Production migration/registration remains with Kaiwu's own contract; no production role, daemon, App, Goal, global trust or timer mutation. #527 remains deferred.
