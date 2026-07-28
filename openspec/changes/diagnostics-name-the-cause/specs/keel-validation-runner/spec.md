## ADDED Requirements

### Requirement: A narrowed refusal is asserted from both sides
When validation covers a diagnostic whose scope this project narrows, the suite MUST assert both the shape that must still be refused and the shape that must now pass. A scenario asserting only the newly passing shape MUST NOT be accepted as coverage, because a check that removed the refusal entirely would also satisfy it.

#### Scenario: A narrowed diagnostic keeps its refusing case
- **WHEN** a scenario covers a diagnostic whose matching scope was narrowed
- **THEN** it asserts that the still-in-scope shape is refused and names that diagnostic
- **AND THEN** it asserts that the out-of-scope shape produces no such diagnostic

#### Scenario: Following the diagnostic resolves the problem it reports
- **WHEN** a scenario covers a diagnostic that tells the author what to change
- **THEN** it applies exactly what the diagnostic names and asserts the same diagnostic no longer appears
