## MODIFIED Requirements

### Requirement: A repository declares delegation in its own block

Keel MUST read optional delegation tiers as execution metadata, not as permission to choose a subagent. An absent or empty declaration MUST leave model-chosen helpers and guarded implementation available without inventing a tier. The authorize vocabulary MUST remain unchanged.

#### Scenario: No declaration needs no extra permission
- **WHEN** no delegation block exists
- **THEN** helper projection succeeds and implementation depends on existing task authority and a matching active guard

### Requirement: Delegation requires an active write-guard manifest

Keel MUST refuse implementation delegation unless guardStatus is active and its change, task and fingerprint match the selected implementation task. File existence alone MUST NOT prove this precondition. Read-only helpers MUST NOT depend on a manifest.

#### Scenario: Mismatched guard refuses writing
- **WHEN** a manifest is present but invalid, drifted or selected for another task
- **THEN** implementation is refused with the actual reason

### Requirement: The delegation brief is write-capable and separate from the helper brief

Implementation posture MUST compile a write-capable brief separate from the read-only helper contract, carrying task, Read, Touch, checks, fingerprint, optional declared tier and prohibitions. The model MUST choose this posture using existing task write authority. Helpers MUST retain mutation refusal and byte-stability checks.

#### Scenario: Task authority bounds a delegate
- **WHEN** implementation is selected with valid task authority and guard but no tier
- **THEN** the brief carries Touch and requires master reruns, with no invented tier or model

### Requirement: Capability tiers are abstract and target-resolved

Keel MUST preserve optional abstract capability tiers as metadata without selecting or claiming to observe a concrete model. It MUST NOT infer a tier from task size or require an undeclared tier as extra permission for implementation.

#### Scenario: No tier is invented
- **WHEN** a task has no declared tier
- **THEN** guarded implementation remains available and the brief states no tier was declared

### Requirement: Delegation authorizes only delegation

Model-chosen delegation MUST keep task scope, gates, Evidence, Review, triage and repository permissions unchanged. Optional metadata MUST NOT trigger spawning, scheduling, scope expansion or ownership transfer.

#### Scenario: Organization does not widen authority
- **WHEN** the current agent chooses helper or implementation posture
- **THEN** task and repository action boundaries remain unchanged

