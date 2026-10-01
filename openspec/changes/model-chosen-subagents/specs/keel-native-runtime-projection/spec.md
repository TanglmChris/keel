## MODIFIED Requirements

### Requirement: Subagent projection preserves Keel ownership

Keel MUST let the current agent choose bounded helper or implementation subagent posture without extra user activation for subagent use. Helper posture MUST be read-only/evidence-only and independent of delegation configuration. Implementation posture MUST require current task write authority and a valid matching active guard; optional tiers MUST remain metadata. The current agent MUST retain task, Acceptance, fallback and completion decisions. Goal and task-view activation MUST remain explicit. Legacy activation flags MAY remain compatible without being required.

#### Scenario: Model chooses a helper
- **WHEN** a task is selected without user subagent activation or a delegation declaration
- **THEN** helper projection is ready and prohibits writes and durable-state decisions

#### Scenario: Model chooses an implementation delegate
- **WHEN** implementation posture is selected for an implementation task with Touch and matching active guard, without a tier declaration
- **THEN** the brief carries the write boundary and fingerprint, requiring master re-verification

#### Scenario: Invalid guard refuses implementation
- **WHEN** a manifest is missing, invalid, drifted, or guards a different task
- **THEN** implementation is refused with its cause, while a read-only helper needs no guard

#### Scenario: Subagent return remains a claim
- **WHEN** a subagent reports completion or passed checks
- **THEN** current-agent Review, rerun verification and completion gates remain required

#### Scenario: Host policy remains authoritative
- **WHEN** host policy disallows a launch
- **THEN** Keel does not bypass it and projection readiness is not reported as an actual launch

