## ADDED Requirements

### Requirement: Projected session state is reported to the user

SessionStart projection is delivered on a model-only channel, so the agent is
the sole reader unless it speaks. The projection MUST therefore instruct the
receiving agent to state the projected context — status, any selection, and
the next action or fallback reason — to the user in its first response of the
session, without waiting to be asked. The instruction MUST be present on every
branch the projection can take, because the branches a user most needs to see
are the degraded ones. Reporting is a disclosure obligation only: it MUST NOT
select an owner, record a fingerprint, start execution, or turn the projection
into authority, and the projection MUST continue to state that it is
disposable and that OpenSpec and Git remain the durable authority.

#### Scenario: Ready projection is disclosed before work begins

- **WHEN** the SessionStart projection resolves a ready context with a selected change and task
- **THEN** the projected context instructs the agent to state that selection and its next action to the user in the agent's first response
- **AND THEN** the instruction does not authorize implementation, selection, or any write

#### Scenario: Non-ready projection is disclosed rather than silently absorbed

- **WHEN** the SessionStart projection resolves a context that is idle, ambiguous, or otherwise not ready
- **THEN** the projected context instructs the agent to state that status and its reasons to the user in the agent's first response
- **AND THEN** the projection still refuses to guess among candidate owners

#### Scenario: Degraded projection still reaches the human

- **WHEN** the SessionStart script emits its bounded fallback for a missing or incompatible Keel CLI, malformed Core output, or a timeout
- **THEN** the fallback text instructs the agent to tell the user that the projection failed and which manual command replaces it
- **AND THEN** the agent does not silently proceed as though continuity were established

#### Scenario: Resident protocol carries the rule without the plugin

- **WHEN** a repository follows the Keel resident protocol and no native plugin projection runs
- **THEN** the resident Session Start rule still requires the agent to state the context result to the user in its first response
- **AND THEN** continuity does not depend on the plugin being installed or loaded for the user to see where the work stands
