## Why

Keel can coordinate a Claude CLI team, but its Codex target reports continuity, guards and host hand-over as manual. A Codex team cannot yet rely on the same role-directed delivery and bounded hand-over without separately verified host integration.

## What Changes

- Bind role sessions to their Codex thread identities and expose their host state without disturbing Claude roles.
- Deliver addressed work to the correct Codex session and resume or hand over safely, including busy, missing, unreachable and repeated delivery cases.
- Verify real Codex lifecycle hooks and guard behavior, including startup, compaction, write boundaries and branch pushes; report capabilities no higher than measured.
- Exercise two real Codex roles through assignment, wake, result and hand-over, subject to host availability and user authorizations.

## Capabilities

### New Capabilities

- `keel-codex-host-team`: Codex role identity, delivery, wake and hand-over via a verified host adapter.

### Modified Capabilities

- `keel-shift-change`: host-specific Codex hand-over.
- `keel-touch-write-guard`: verified Codex hook coverage and denial.
- `keel-stateless-continuity`: Codex startup and compaction projection.

## Impact

Codex hooks, chat and shift host adapters, capability reporting, validation and documentation. Host trust, permissions, failure recovery, duplicate delivery and concurrent activity require explicit evidence. Existing Claude behavior and its established routing stay intact. #527 is explicitly deferred.
