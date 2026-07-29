## ADDED Requirements

### Requirement: A repository declares standing authorization in a closed vocabulary

Keel MUST read an optional `authorize:` declaration from `keel/config.yaml` naming repository
actions the owner has authorized to proceed without a per-occurrence confirmation. The accepted
action names MUST be a closed set — `commit`, `push`, `release`, `archive` — and an absent, empty,
or undeclared block MUST leave every action unauthorized.

#### Scenario: A declared action is authorized for the whole repository
- **WHEN** `keel/config.yaml` declares `authorize:` listing `commit` and `push`
- **THEN** Keel resolves `commit` and `push` as standing-authorized for that repository
- **AND THEN** `release` and `archive` remain unauthorized because they were not listed

#### Scenario: No declaration preserves current behavior
- **WHEN** `keel/config.yaml` is absent, or declares no `authorize:` block, or declares an empty one
- **THEN** no action is standing-authorized
- **AND THEN** every autonomy default resolves exactly as it does without this capability

#### Scenario: An unrecognized action name is reported, not granted
- **WHEN** the `authorize:` block lists a name outside the closed set
- **THEN** Keel reports a configuration error naming the offending entry and the accepted names
- **AND THEN** the unrecognized entry authorizes nothing, and is not silently dropped

### Requirement: A task inherits standing authorization only where it authored none

Keel MUST apply a standing authorization as the default a task did not author. A task that
declares its own `Autonomy boundary:` MUST keep that boundary unchanged, and a standing
authorization MUST NOT override, widen, or narrow it.

#### Scenario: A task without an authored boundary inherits the declaration
- **WHEN** a task declares no `Autonomy boundary:` and the repository authorizes `commit`
- **THEN** the compiled capsule resolves `commit` as authorized instead of `Default: hard-stop`
- **AND THEN** actions the repository did not declare still resolve to hard-stop

#### Scenario: An authored boundary wins over the declaration
- **WHEN** a task declares an explicit `Autonomy boundary:` and the repository declares an
  `authorize:` block
- **THEN** the compiled capsule carries the task's authored boundary
- **AND THEN** the repository declaration does not alter it

#### Scenario: The capsule names where an authorization came from
- **WHEN** a capsule carries an authorization inherited from the repository declaration
- **THEN** the capsule and the gate result identify the repository declaration as its source
- **AND THEN** a reader can distinguish an inherited authorization from a task-authored one

### Requirement: Standing authorization covers the action and never its proof

Keel MUST NOT let a standing authorization weaken, skip, or make conditional any gate, evidence
requirement, semantic Review, or write guard. A standing authorization MUST authorize only the
decision to proceed with a named action once its own checks have passed.

#### Scenario: A failing gate still stops a declared action
- **WHEN** `push` is standing-authorized and the task's completion gate returns `fail` or
  `needs-review`
- **THEN** the gate result is unchanged by the declaration
- **AND THEN** the action does not proceed on the strength of the authorization

#### Scenario: A declaration does not suppress reporting
- **WHEN** an action proceeds under a standing authorization
- **THEN** its command evidence, gate result, and Review are recorded exactly as they would be
  without the declaration
- **AND THEN** the declaration removes the confirmation, not the record

#### Scenario: A declaration is not a trigger
- **WHEN** an action is standing-authorized but the workflow has not reached the point where that
  action occurs
- **THEN** Keel does not initiate the action
- **AND THEN** no scheduler, backlog selection, or next-task inference is implied by the
  authorization
