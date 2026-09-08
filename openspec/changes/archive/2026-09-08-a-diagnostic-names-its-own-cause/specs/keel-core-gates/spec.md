## ADDED Requirements

### Requirement: A reference is judged against what the task declares

When Keel judges a reference to an `M<n>` check, it MUST resolve the declared set from the
verification form the task itself declares. Keel MUST NOT report a reference as naming an
undeclared check because the task's contract did not compile.

A problem with one check's declaration MUST be reported as that problem alone.

#### Scenario: A malformed check does not disown its own references

- **WHEN** a task's `M<n>` declaration carries an unfilled slot and its Findings resolves a finding to that same `M<n>`
- **THEN** the gate reports the unfilled slot
- **AND THEN** it does not report the reference as naming a check the task does not declare

### Requirement: task-start states the red-green obligation

When a task declares a strategy requiring red-green execution, `keel gate task-start` MUST report
which of its checks will require `.red` and `.green` Evidence at completion, and which are exempt.

This MUST be a warning: `task-start` MUST NOT refuse a task for an obligation that belongs to
completion, and what completion requires MUST NOT change.

#### Scenario: The obligation is stated when the contract is accepted

- **WHEN** `task-start` accepts a task whose strategy requires red-green execution
- **THEN** it warns which checks will owe `.red` and `.green` Evidence
- **AND THEN** the task still passes

#### Scenario: A strategy without red-green says nothing

- **WHEN** `task-start` accepts a task whose strategy does not require red-green execution
- **THEN** it reports no red-green obligation

### Requirement: A shared explanation is printed once

When several gate problems share one rule explanation, the rendered text MUST print each problem
and MUST print each distinct explanation once rather than once per problem.

The machine-readable result MUST carry the explanation with every problem it belongs to.

#### Scenario: One explanation, several violations

- **WHEN** a gate reports several problems that share a rule explanation
- **THEN** the rendered text contains that explanation exactly once
- **AND THEN** each problem's own text still names the item it is about

#### Scenario: The JSON result is not deduplicated

- **WHEN** the same gate runs with `--json`
- **THEN** every problem carries its own explanation
