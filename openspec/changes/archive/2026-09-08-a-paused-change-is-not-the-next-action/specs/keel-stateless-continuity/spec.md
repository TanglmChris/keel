## ADDED Requirements

### Requirement: A change its owner paused is not inferred as the next action

A change MAY declare itself paused in its own OpenSpec change configuration, under a Keel-owned
key, together with a reason.

`keel context` MUST NOT infer a paused change as the next action. It MUST name each paused change
it skipped and report that change's reason, and MUST NOT skip one silently. When every active
change is paused, Keel MUST report that there is nothing to infer and list each paused change with
its reason, rather than reporting that no change exists.

Explicit selection MUST still reach a paused change, reporting that it is paused.

Pausing MUST NOT change what any gate, the write guard, or completion does. Keel MUST NOT pause a
change on its own.

A declaration Keel cannot read MUST leave the change unpaused and MUST be reported.

#### Scenario: Inference passes over a paused change

- **WHEN** one active change is paused and another is not
- **THEN** `keel context` selects the change that is not paused
- **AND THEN** it names the paused change and its reason

#### Scenario: Every change is paused

- **WHEN** every active change is paused
- **THEN** `keel context` reports that there is nothing to infer
- **AND THEN** it lists each paused change with its reason

#### Scenario: The owner selects a paused change

- **WHEN** `keel context --change` names a paused change
- **THEN** Keel selects it and reports that it is paused

#### Scenario: Pausing is not a gate

- **WHEN** a gate runs against a task of a paused change
- **THEN** its verdict is what it would be if the change were not paused

#### Scenario: An unreadable declaration pauses nothing

- **WHEN** a change's Keel configuration cannot be read as a pause declaration
- **THEN** the change stays available to inference
- **AND THEN** Keel reports that the declaration could not be read
