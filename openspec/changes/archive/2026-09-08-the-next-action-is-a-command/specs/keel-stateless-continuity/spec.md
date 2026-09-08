## ADDED Requirements

### Requirement: The next action is reported as a command

When `keel context` reports a next action that has a command, it MUST report the invocation that
runs it, including every argument that invocation requires, and MUST carry the same string in its
machine-readable result.

The reported command MUST name its change and task explicitly rather than relying on inference.

Keel MUST NOT run the reported command.

#### Scenario: A gate action reports its invocation

- **WHEN** `keel context` reports a next action of `task-start`, `task-complete`, or `change-close`
- **THEN** it reports the command that runs it
- **AND THEN** the command names the change and the task explicitly

#### Scenario: A required argument appears in the command

- **WHEN** the next action is `change-close`
- **THEN** the reported command includes the action argument that `change-close` requires

#### Scenario: An action with no command reports none

- **WHEN** the next action has no command to run
- **THEN** Keel reports no command rather than an empty one
