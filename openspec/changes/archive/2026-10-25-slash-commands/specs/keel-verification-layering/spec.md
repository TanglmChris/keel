## MODIFIED Requirements

### Requirement: Keel documents how to choose a Verify strategy

The `tdd-or-test-first` skill MUST state that a task's Verify strategy is chosen by what would make
its resolved Acceptance false, and that the task's size, apparent risk, the executing model, and the
cost of running a red do not choose it. Its guidance MUST give a selection row for every strategy the
task parser accepts, with worked examples of a right and a wrong choice, and the skill MUST name every
evidence clause the completion gate enforces — `Fails with:`, `Detects:`, `Measured:`, the
`(regression)` tag with `deferred to C<n>`, and `artifact` Evidence — so each is found from the skill
an executor loads when it plans its checks.

#### Scenario: Every accepted strategy has a selection row
- **WHEN** the task parser accepts a Verify strategy
- **THEN** the test-first skill's guidance names it in its selection table

#### Scenario: Every enforced evidence clause is named in the skill
- **WHEN** an executor loads `tdd-or-test-first`
- **THEN** its body names `Fails with:`, `Detects:`, `Measured:`, `(regression)`, `deferred to C`, and `artifact`
- **AND THEN** the plugin copy is identical to the canonical skill and guidance
