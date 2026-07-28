## ADDED Requirements

### Requirement: A task body ends at the next task or the next heading
Task parsing MUST end a task's body at the next task or at the next `##` heading, whichever comes first, so that a change-level section is never read as a field of the preceding task. Every consumer of a task's extent MUST use that same boundary rather than recomputing one.

#### Scenario: A change-level section is not the last task's Evidence
- **WHEN** a tasks file declares `## Invalidates` or `## Expectation Coverage` after its last task
- **THEN** that section's lines are not appended to any task field
- **AND THEN** an unfilled-slot token quoted inside the section does not make the last task's `Evidence` non-concrete

#### Scenario: A group heading is not the previous task's field
- **WHEN** a tasks file declares a task group heading between two tasks
- **THEN** that heading is not appended to the preceding task's last field

#### Scenario: A quoted invalidation phrase satisfies both checks
- **WHEN** an `## Invalidates` entry quotes stale wording that contains an unfilled-slot token
- **THEN** the double-quoted phrase satisfies the searchable-phrase check
- **AND THEN** the same text does not make any task's `Evidence` non-concrete

#### Scenario: The anchor search uses the task's own extent
- **WHEN** the `Contract` anchor of the last task is located for recording
- **THEN** the search covers only that task's body and does not reach a trailing section
