## ADDED Requirements

### Requirement: SessionStart projection reaches the human directly

The SessionStart projection MUST emit a human-visible message on the host's
supported hook-output channel, carrying the projected status, any selection,
and the next command, in addition to the model-facing context payload. The
human message MUST be produced on every branch the projection can take,
including the degraded fallbacks, because a hook that fails silently is
indistinguishable from a hook that never ran. The human message MUST NOT
replace the model-facing payload or the instruction that the agent restate the
projection: one channel tells the human what the state is, the other keeps the
agent accountable for acting on it.

Emitting the human message MUST NOT change the hook's existing discipline. The
hook MUST still exit 0, MUST NOT block the session, MUST NOT write project
state, and MUST NOT select an owner among ambiguous candidates. When the host
does not support the channel, the projection MUST degrade to the model-facing
payload alone rather than failing.

#### Scenario: Ready projection is visible without a user message
- **WHEN** the SessionStart projection resolves a ready context with a selected change and task
- **THEN** the hook output carries a human-visible message naming that selection and its next command
- **AND THEN** the model-facing context payload is emitted unchanged in the same output

#### Scenario: Non-ready projection is visible to the human
- **WHEN** the SessionStart projection resolves an idle, ambiguous, or blocked context
- **THEN** the hook output carries a human-visible message naming that status and the explicit next command
- **AND THEN** the message does not name a guessed owner among candidates

#### Scenario: Degraded projection is visible rather than silent
- **WHEN** the SessionStart script emits its bounded fallback for a missing or incompatible Keel CLI, malformed Core output, or a timeout
- **THEN** the hook output carries a human-visible message stating that the projection failed and which manual command replaces it
- **AND THEN** the hook still exits 0 and leaves the session usable

#### Scenario: The human channel authorizes nothing
- **WHEN** a human-visible projection message is emitted for any status
- **THEN** no task is selected, no fingerprint is recorded, no goal is created, and no project state is written
- **AND THEN** the message states that the projection is disposable and that OpenSpec and Git remain the durable authority

## MODIFIED Requirements

### Requirement: Projected session state is reported to the user

SessionStart projection carries a model-facing payload that only the agent
reads. The projection MUST therefore instruct the receiving agent to state the
projected context — status, any selection, and the next action or fallback
reason — to the user in its first response of the session, without waiting to
be asked. The instruction MUST be present on every branch the projection can
take, because the branches a user most needs to see are the degraded ones.

This instruction is not the only path to the human, and MUST NOT be treated as
one. It covers what the direct human channel cannot: it makes the agent act on
the state it was given, and it reaches a user whose host renders no hook
message. Reporting is a disclosure obligation only: it MUST NOT select an
owner, record a fingerprint, start execution, or turn the projection into
authority, and the projection MUST continue to state that it is disposable and
that OpenSpec and Git remain the durable authority.

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

#### Scenario: The agent restates the projection even when the host showed it
- **WHEN** the host renders the projection's human-visible message directly and the agent also receives the model-facing payload
- **THEN** the agent still states the projected context in its first response
- **AND THEN** the two channels are not treated as redundant, because the agent's restatement is what shows the user which state the agent is actually working from
