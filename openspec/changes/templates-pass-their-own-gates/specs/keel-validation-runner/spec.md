## ADDED Requirements

### Requirement: A shipped template is validated by the tool that consumes it
Validation MUST assert each shipped schema template by filling its author-facing slots and running the tool that consumes its output — `openspec validate` for a spec template, the `task-start` gate for a tasks template — rather than by matching the template's prose. A prose assertion MUST NOT be accepted as coverage, because a template that only mentions a requirement in a comment satisfies it while still failing for the author who copies it.

#### Scenario: A copied template passes the gate that consumes it
- **WHEN** a shipped template's author-facing slots are filled with concrete text and the result is presented to the tool that consumes it
- **THEN** that tool reports no error
- **AND THEN** the assertion is made through that tool rather than by matching the template's own wording

#### Scenario: The template drifts from the rule it illustrates
- **WHEN** a shipped template's example no longer satisfies the gate that reads it
- **THEN** validation fails and names the diagnostics the filled template produced

#### Scenario: The consuming tool is unavailable
- **WHEN** a template's consuming tool is not on PATH
- **THEN** the scenario reports the skip rather than passing silently or failing

### Requirement: A shipped tasks template carries a worked example of every strategy shape it documents
A shipped tasks template MUST show a worked example of each Evidence shape its prose requires, not the prose alone. For a red-green strategy that means a concrete check carrying its bare, `.red`, and `.green` Evidence entries, and a `regression`-tagged check carrying only its bare entry, with at least one check left untagged.

#### Scenario: The red-green shape is shown, not only described
- **WHEN** an author reads the shipped tasks template to write a red-green task
- **THEN** the template shows a strategy line, an untagged check with its bare, `.red`, and `.green` Evidence entries, and a `regression`-tagged check with only its bare entry
- **AND THEN** the example passes `task-start` once its slots are filled
