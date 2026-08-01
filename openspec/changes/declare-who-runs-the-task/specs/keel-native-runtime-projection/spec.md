## MODIFIED Requirements

### Requirement: Subagent projection preserves Keel ownership

Keel MAY use native subagent lifecycle surfaces only when the user or selected task explicitly authorizes bounded delegation. The current agent MUST retain Keel execution, acceptance, fallback, and completion decisions. Where the authorization permits implementation, the projected brief MUST state the `Touch` write boundary and the declared capability tier explicitly rather than leaving the boundary to be inferred.

#### Scenario: Authorized subagent receives bounded context
- **WHEN** an authorized subagent starts
- **THEN** it receives only the selected task, required Read context, applicable Touch or read-only boundary, and requested evidence contract
- **AND THEN** it is not authorized to change Acceptance, mark tasks complete, sync, archive, or transfer Keel ownership

#### Scenario: An implementing subagent receives its write boundary and tier
- **WHEN** an authorized subagent starts under a declaration permitting implementation
- **THEN** the brief states the `Touch` write boundary, the capsule fingerprint, and the declared capability tier
- **AND THEN** it states that the tier is carried to the target and that Keel does not select or observe a model

#### Scenario: Subagent return is evidence only
- **WHEN** an authorized subagent stops
- **THEN** its result is treated as report or evidence for current-agent review
- **AND THEN** native subagent completion does not satisfy `task-complete`

#### Scenario: An implementing subagent's reported results are re-run
- **WHEN** an authorized subagent that was permitted to implement reports its verification checks passed
- **THEN** the current agent re-runs each `M<n>` check and records its own results as Evidence
- **AND THEN** the subagent's reported results are not recorded as Evidence

#### Scenario: No implicit delegation
- **WHEN** the user and selected task have not authorized subagent use
- **THEN** Keel does not spawn or activate one merely because the runtime supports it
