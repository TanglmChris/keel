## MODIFIED Requirements

### Requirement: Task modes and conditional fields are executable
Keel MUST validate task mode and conditional fields as behavior, not unchecked labels. Where a diagnostic requires the author to add a field, it MUST name that field and its exact line prefix rather than describing the authority abstractly. A task whose whole effect is an authorized repository-level action and which writes no worktree file MUST have a legal mode of its own, rather than being forced to name a Touch path it does not write.

#### Scenario: Diagnose-only has no product Touch
- **WHEN** a task declares `Mode: diagnose-only` and `Touch: none`
- **THEN** the capsule accepts the contract and prohibits product writes
- **AND THEN** `task-start` does not reject the literal `none` as an unspecified placeholder

#### Scenario: Repo-action performs a repository action without worktree writes
- **WHEN** a task declares `Mode: repo-action` and `Touch: none`
- **THEN** the capsule accepts the contract, prohibits product writes, and is the one mode that does not prohibit committing, because performing that action is the task
- **AND THEN** the mode is recorded in the compiled capsule, so the authorization is visible in the fingerprint rather than inferred from an empty field

#### Scenario: Repo-action still refuses a product Touch
- **WHEN** a task declares `Mode: repo-action` with a concrete Touch path
- **THEN** compilation fails, naming the `Touch: none` the mode requires
- **AND THEN** an unsupported mode value is still rejected by a diagnostic listing every supported mode

#### Scenario: Implementation requires concrete Touch
- **WHEN** an implementation task has no concrete Touch path
- **THEN** compilation fails before task execution

#### Scenario: Coupling fields are conditional
- **WHEN** coupling is none
- **THEN** candidate-only coupling fields are absent or rejected as contradictory
- **AND WHEN** coupling is required
- **THEN** the capsule requires the design Coupled Iteration Contract and task candidate boundaries, stop rules, final assertions, and evidence contract

#### Scenario: Authority diagnostic names the field to add
- **WHEN** a task's `Covers` references an unresolved `Q<n>` and no authorized fallback is declared on the task
- **THEN** the `unresolved-authority` diagnostic names the `Autonomy boundary:` field and the `Pre-authorized fallback:` line prefix it requires
- **AND THEN** the diagnostic does not imply that prose in `design.md` satisfies the check
