# keel-authorized-delegation Specification

## Purpose

Declares who runs an OpenSpec task — the current agent or an authorized delegate — under what precondition, and what a delegate's result may settle.

## Requirements
### Requirement: A repository declares delegation in its own block

Keel MUST read optional delegation tiers as execution metadata, not as permission to choose a subagent. An absent or empty declaration MUST leave model-chosen helpers and guarded implementation available without inventing a tier. The authorize vocabulary MUST remain unchanged.

#### Scenario: No declaration needs no extra permission
- **WHEN** no delegation block exists
- **THEN** helper projection succeeds and implementation depends on existing task authority and a matching active guard

### Requirement: A task inherits the delegation declaration only where it authored none

Keel MUST apply the repository delegation declaration as the default a task did not author. A task that authors its own delegation entry MUST keep it unchanged, and the compiled capsule MUST name `keel/config.yaml` as the source of any entry the declaration supplied.

#### Scenario: A silent task inherits the repository default
- **WHEN** a task authors no delegation entry and `keel/config.yaml` declares one
- **THEN** the compiled capsule carries the declared tier
- **AND THEN** the capsule names `keel/config.yaml` as that entry's source

#### Scenario: A task that authored its own entry keeps it
- **WHEN** a task authors a delegation entry and `keel/config.yaml` declares a different one
- **THEN** the compiled capsule carries the task's entry unchanged
- **AND THEN** the declaration does not override, merge with, or annotate it

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

### Requirement: A delegate's return is a claim the current agent re-verifies

Keel MUST treat a delegate's reported command results as a claim rather than evidence. The current agent MUST re-run each `M<n>` verification check itself before recording Evidence, and a delegate's completion MUST NOT satisfy `task-complete`, mark the task checkbox, or settle Review.

#### Scenario: Reported results are not recorded as Evidence
- **WHEN** a delegate returns reporting that its verification checks passed
- **THEN** the current agent re-runs each `M<n>` check and records its own results as Evidence
- **AND THEN** the delegate's reported results are not recorded as Evidence

#### Scenario: Byte-identity verification is unavailable for a writer
- **WHEN** a delegate that was authorized to write returns
- **THEN** the repository byte-identity check that validates a read-only helper return does not apply, because writing is what the delegate was authorized to do
- **AND THEN** re-running the verification checks is what restores current-agent evidence

#### Scenario: A delegate cannot complete a task
- **WHEN** a delegate reports the selected task finished
- **THEN** completion still requires `keel gate task-complete`, current-agent Review, and the current agent's own checkbox write
- **AND THEN** the delegate's report settles none of them

### Requirement: Capability tiers are abstract and target-resolved

Keel MUST preserve optional abstract capability tiers as metadata without selecting or claiming to observe a concrete model. It MUST NOT infer a tier from task size or require an undeclared tier as extra permission for implementation.

#### Scenario: No tier is invented
- **WHEN** a task has no declared tier
- **THEN** guarded implementation remains available and the brief states no tier was declared

### Requirement: An unavailable tier refuses delegation rather than substituting one

Keel MUST refuse delegation when the current target cannot provide the declared tier, and MUST report the declared tier beside what the target offers. Keel MUST NOT silently substitute a different tier.

#### Scenario: An unprovidable tier is reported, not substituted
- **WHEN** the declared tier is not among those the current target provides
- **THEN** Keel refuses the delegation and reports the declared tier and the available ones
- **AND THEN** no work runs at a tier the owner did not declare

### Requirement: Delegation authorizes only delegation

Model-chosen delegation MUST keep task scope, gates, Evidence, Review, triage and repository permissions unchanged. Optional metadata MUST NOT trigger spawning, scheduling, scope expansion or ownership transfer.

#### Scenario: Organization does not widen authority
- **WHEN** the current agent chooses helper or implementation posture
- **THEN** task and repository action boundaries remain unchanged
