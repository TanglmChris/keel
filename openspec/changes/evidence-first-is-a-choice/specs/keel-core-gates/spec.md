## ADDED Requirements

### Requirement: task-start refuses an undeclared strategy and an unjustified evidence-first

`keel gate task-start` MUST refuse a task that declares a verification form but names no
verification strategy, and MUST name the supported strategies in the refusal. It MUST refuse a
task whose strategy is `evidence-first` and that states no reason, or states a placeholder, that a
meaningful red-green loop does not apply.

The reason MUST be declared beside the strategy under the task's verification field, MUST compile
into the capsule as part of the verification block, and MUST NOT be parsed as a check. Keel MUST
validate that the reason is present and concrete and MUST NOT judge whether it is true; the stated
reason is reviewed by the semantic Review, not by the gate.

No mode, tag, or other field MUST exempt a task from stating the reason.

#### Scenario: A task names no strategy

- **WHEN** `task-start` compiles a task that declares `Verify` or `Commands` but no strategy
- **THEN** it returns `fail` and names the supported strategies
- **AND THEN** it does not report the task as using `evidence-first`

#### Scenario: An evidence-first task states no reason

- **WHEN** `task-start` compiles a task declaring `evidence-first` with no reason, or with a placeholder reason
- **THEN** it returns `fail` and names the reason as what is missing

#### Scenario: An evidence-first task states its reason

- **WHEN** an `evidence-first` task declares a concrete reason beside its strategy
- **THEN** `task-start` passes and the compiled capsule carries the reason in its verification block
- **AND THEN** the reason is not parsed as a check and takes no `M<n>` Evidence label

#### Scenario: A red-green task needs no reason

- **WHEN** a task declares vertical-tdd, regression-first, characterization, snapshot-characterization, or rendered-behavior
- **THEN** `task-start` does not require a reason
