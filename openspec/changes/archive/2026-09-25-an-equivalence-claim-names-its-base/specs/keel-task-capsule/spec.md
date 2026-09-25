# keel-task-capsule

## ADDED Requirements

### Requirement: A zero-difference claim names its base and its fields

`Verify` SHALL accept `equivalence` as a strategy for work whose criterion is that a measured result
does not change. An `equivalence` task SHALL declare `Base:` — a resolvable git ref — and `Fields:` —
the compared field set — beside `Strategy:`, and SHALL require no red-green evidence. `keel gate
task-start` SHALL refuse a missing `Base:`, a missing or empty `Fields:`, a `Base:` that no git ref
resolves, and a `Base:` that resolves to the same commit as `HEAD`.

#### Scenario: The strategy is accepted without a red

- **WHEN** a task declares `Strategy: equivalence` with a resolvable `Base:` and a non-empty `Fields:`
- **THEN** `keel gate task-start` passes
- **AND** no `.red` or `.green` Evidence is required at completion

#### Scenario: A base that is head compares nothing

- **WHEN** an `equivalence` task's `Base:` resolves to the same commit as `HEAD`
- **THEN** `keel gate task-start` fails, naming the resolved commit
- **AND** the refusal states that an A/B against itself always agrees

#### Scenario: A missing declaration is named

- **WHEN** an `equivalence` task omits `Base:` or declares an empty `Fields:`
- **THEN** `keel gate task-start` fails, naming the missing declaration

### Requirement: Equivalence is not an escape from red-green

An `equivalence` task whose `Covers` names a scenario belonging to an `## ADDED Requirements` delta
SHALL be refused unless another task of the same change declares a red-green strategy and covers that
same scenario.

#### Scenario: New behavior needs a red somewhere in the change

- **WHEN** an `equivalence` task covers a scenario from an `## ADDED Requirements` delta and no other
  task of the change covers it under a red-green strategy
- **THEN** `keel gate task-start` fails, naming the scenario
- **AND** the refusal states that behavior which is new is not behavior which is unchanged

#### Scenario: A sibling red-green task satisfies it

- **WHEN** another task of the same change declares `vertical-tdd` and covers that scenario
- **THEN** `keel gate task-start` passes

### Requirement: Evidence may reference an artifact instead of retelling it

A check's Evidence MAY read `artifact <path> sha256:<digest>` in place of prose. `keel gate
task-complete` SHALL check that the path exists and that its digest matches, and SHALL refuse a path
outside the change's own directory.

#### Scenario: A matching digest is accepted

- **WHEN** a check's Evidence names an artifact inside the change directory whose digest matches
- **THEN** `keel gate task-complete` accepts it as concrete Evidence

#### Scenario: A stale digest is refused

- **WHEN** the artifact's content no longer matches the recorded digest
- **THEN** `keel gate task-complete` fails, naming the path and both digests

#### Scenario: A path that archiving would leave behind is refused

- **WHEN** the artifact path is outside the change's own directory
- **THEN** `keel gate task-complete` fails, stating that archiving moves the change directory
