## ADDED Requirements

### Requirement: A dry run accounts for every write its real run would make

A dry run exists so a reader can decide whether to proceed. It is therefore held
to both directions of accuracy: it MUST name every write the corresponding real
run would perform, and it MUST NOT name a write that would not happen. A dry run
that under-reports offers a promise it does not keep, and one that over-reports
trains the reader to ignore it — both leave the reader worse off than no dry run,
because both are relied upon.

Where a real run performs a step outside the plan the dry run enumerates, that
step MUST be represented in the dry run too. Where a dry run classifies work as
pending, it MUST determine that from the same computation the real run uses,
rather than from a separate listing that can drift from it.

#### Scenario: The plan covers steps the enumerated plan does not

- **WHEN** a real run performs a write through a step outside its enumerated action plan
- **THEN** the dry run reports that step's writes alongside the enumerated ones
- **AND THEN** a reader of the dry run is not surprised by a file the real run changes

#### Scenario: A dry run does not claim writes that will not happen

- **WHEN** a dry run inspects a set of surfaces of which only some need changing
- **THEN** it names only the ones that would change, and summarises the rest as current
- **AND THEN** its counts match what the real run reports afterwards

#### Scenario: Both paths share one definition of pending work

- **WHEN** the dry run and the real run classify the same surface
- **THEN** they agree, because the classification is computed the same way in both
- **AND THEN** a change to what counts as current cannot move one without the other
