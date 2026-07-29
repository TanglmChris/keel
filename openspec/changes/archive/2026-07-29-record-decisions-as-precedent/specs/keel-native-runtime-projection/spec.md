## MODIFIED Requirements

### Requirement: Native plugin SessionStart projects shared context
Codex and Claude native plugins MUST map their supported SessionStart lifecycle to shared Keel context projection through one plugin script. The script MUST treat OpenSpec/Git and the current task capsule as authority and MUST return only disposable runtime context. Where a precedent store is declared, the projection MUST carry a pointer to it — its size, how much of it is authorized, and how current it is — and MUST NOT carry any precedent body.

#### Scenario: Codex SessionStart maps to shared Core
- **WHEN** a trusted Codex plugin SessionStart hook fires
- **THEN** the plugin script invokes the shared Keel projection for the current checkout
- **AND THEN** Codex receives concise additional context without a target-local task parser

#### Scenario: Claude SessionStart maps to shared Core
- **WHEN** an allowed Claude plugin SessionStart hook fires
- **THEN** the same plugin script invokes the shared Keel projection for the current checkout
- **AND THEN** Claude receives equivalent concise authority through its supported hook output

#### Scenario: SessionStart never starts execution
- **WHEN** either runtime receives the startup projection
- **THEN** the hook does not select a task among ambiguous owners, record a fingerprint, spawn a helper, create a goal, write evidence, or continue a turn automatically

#### Scenario: A declared precedent store projects as a pointer
- **WHEN** a precedent store is declared and the SessionStart projection is produced
- **THEN** the projection states how many precedents exist, how many are authorized, and when the store was last synced
- **AND THEN** no precedent body, decision text, or rationale appears in the projection

#### Scenario: An undeclared store adds nothing to the projection
- **WHEN** no precedent store is declared
- **THEN** the projection is byte-identical to the projection produced without this capability
- **AND THEN** the hook performs no filesystem search for a store it was not told about
