## MODIFIED Requirements

### Requirement: Keel compiles compact tasks into a complete execution capsule
Keel MUST accept a compact v4 task source and compile it with versioned defaults and referenced OpenSpec authority into `keel-task-capsule/v1`. The capsule MUST be complete enough for the current agent to execute without guessing and MUST remain a disposable view of OpenSpec rather than a new source of truth. Where the repository declares standing authorization, the capsule MUST resolve the autonomy default from that declaration and MUST name it as the source. Where the repository declares delegation, the capsule MUST resolve the delegation default the same way and MUST name it as the source.

#### Scenario: Normal implementation task inherits defaults
- **WHEN** a task declares resolvable `Covers`, concrete `Touch`, and `Verify` with a supported strategy and at least one `M<n>` check
- **THEN** the capsule supplies default implementation mode, current-agent ownership, base Read context, hard-stop autonomy, no coupling, read-only helper authority, no delegation, standard prohibitions, and derived Acceptance
- **AND THEN** the source task is not required to repeat those defaults

#### Scenario: Repository-declared authorization replaces the hard-stop default
- **WHEN** a task declares no `Autonomy boundary:` and `keel/config.yaml` standing-authorizes an action
- **THEN** the capsule resolves that action as authorized in place of the hard-stop default
- **AND THEN** the capsule records the repository declaration as the source of that entry
- **AND THEN** every action the declaration does not name still resolves to hard-stop

#### Scenario: Repository-declared delegation replaces the no-delegation default
- **WHEN** a task declares no delegation entry and `keel/config.yaml` declares `delegation:`
- **THEN** the capsule resolves the declared tier in place of the no-delegation default
- **AND THEN** the capsule records `keel/config.yaml` as the source of that entry
- **AND THEN** read-only helper authority is unchanged, because a delegate and a helper are distinct roles

#### Scenario: A task's own delegation entry is not overridden
- **WHEN** a task authors a delegation entry and `keel/config.yaml` declares a different one
- **THEN** the capsule carries the task's entry unchanged and names the task as its source
- **AND THEN** the repository declaration supplies nothing for that task

#### Scenario: Non-default behavior is explicit
- **WHEN** a task needs diagnose-only, plan-first, coupling, additional Read paths, an authorized fallback, or a task-specific Acceptance delta
- **THEN** the source task declares only the applicable non-default clauses
- **AND THEN** the capsule includes their normalized executable meaning

#### Scenario: Incomplete capsule does not compile
- **WHEN** a required reference, field, conditional clause, or default cannot be resolved uniquely
- **THEN** compilation returns structured diagnostics without a usable capsule
- **AND THEN** no consumer substitutes guessed values
