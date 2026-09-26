# keel-merge-declaration

## ADDED Requirements

### Requirement: A repository declares who merges

A repository MAY declare `merge:` in `keel/config.yaml` as `human` or `repository:<check>`, where
`<check>` names the required status check the repository merges on. `keel context` SHALL report a
readable declaration, and for `repository:` SHALL state that no human reviews before merge and that the
named check is the last gate. An absent declaration SHALL add nothing to the projection.
`keel --doctor` SHALL report the declaration, including its absence.

#### Scenario: A repository merge is reported with its consequence

- **WHEN** `keel/config.yaml` declares `merge: repository:full-gate`
- **THEN** `keel context` reports a `Merge:` line naming `full-gate`
- **AND** the line states that no human reviews before merge

#### Scenario: An absent declaration adds nothing

- **WHEN** no `merge:` is declared
- **THEN** `keel context` prints no `Merge:` line
- **AND** `keel --doctor` reports the declaration as absent

### Requirement: A merge claim names its basis

A bare `merge: repository`, or any value outside the accepted forms, SHALL be reported as unreadable,
naming the value and the accepted forms, and SHALL claim nothing.

#### Scenario: A bare repository claim is refused

- **WHEN** `keel/config.yaml` declares `merge: repository`
- **THEN** the projection makes no merge claim
- **AND** a warning names the value and the accepted forms

### Requirement: The declaration is not a permission

The `merge:` declaration SHALL grant the agent nothing. `authorize: merge` SHALL remain an unrecognized
action.

#### Scenario: authorize merge stays unknown

- **WHEN** `keel/config.yaml` lists `merge` under `authorize:`
- **THEN** it is reported as an unrecognized action and authorizes nothing
