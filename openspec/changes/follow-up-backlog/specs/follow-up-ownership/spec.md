## ADDED Requirements

### Requirement: Deferred follow-ups have a durable owner

Project-related follow-ups that are intentionally not done in the current task MUST be recorded in `openspec/changes/follow-up-backlog/tasks.md`, a more specific OpenSpec change, archive evidence, or an explicit discard reason. `keel/HANDOFF.md` MUST NOT be the durable owner for actionable follow-ups.

#### Scenario: Capturing an out-of-scope follow-up

- **GIVEN** an agent identifies project-related work that should not be done in the current task
- **WHEN** the work is actionable enough to track
- **THEN** the agent records it in `openspec/changes/follow-up-backlog/tasks.md` or opens a more specific OpenSpec change
- **AND** the record includes evidence, rationale, proposed owner, and consequence if unchanged.

#### Scenario: Keeping handoff pointer-only

- **GIVEN** a follow-up is relevant to a future session
- **WHEN** `keel/HANDOFF.md` needs to mention it
- **THEN** `keel/HANDOFF.md` only points to the durable owner
- **AND** the actionable follow-up details remain outside `keel/HANDOFF.md`.
