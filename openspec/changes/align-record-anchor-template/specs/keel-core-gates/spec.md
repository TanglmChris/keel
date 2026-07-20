## ADDED Requirements

### Requirement: The tasks template emits a record-compatible Contract anchor

The shipped `keel-spec-driven` tasks template MUST emit the Contract evidence
anchor as the literal line `- Contract: pending`, so that `keel gate task-start
--record` can anchor a freshly-scaffolded task without manual editing. Validation
MUST enforce that the template's anchor stays in this record-compatible form.

#### Scenario: Fresh scaffold is record-able

- **WHEN** a task is scaffolded from the shipped tasks template and `task-start` passes with `--record`
- **THEN** the gate finds the literal `- Contract: pending` anchor and replaces it with the compiled fingerprint line
- **AND THEN** no manual editing of the anchor is required first

#### Scenario: Template anchor form is validated

- **WHEN** validation inspects the shipped tasks template
- **THEN** it requires the Contract anchor to be the literal `- Contract: pending`
- **AND THEN** it does not require a descriptive suffix that the `--record` matcher would reject
