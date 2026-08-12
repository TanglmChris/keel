## ADDED Requirements

### Requirement: Unresolved critical-statement Covers references distinguish missing from unparsed
Keel MUST report a `D<n>`/`F<n>`/`A<n>`/`Q<n>` Covers reference that fails to resolve against `design.md` as missing when the identifier is textually absent from the file, and as unparsed — naming the required line shape — when the identifier is present in the file but not in that shape.

#### Scenario: Identifier absent from design.md is reported as missing
- **WHEN** a task's Covers references a critical-statement identifier that does not appear anywhere in the change's `design.md`
- **THEN** `keel gate task-start` fails with a message reporting the identifier as missing

#### Scenario: Identifier present but mis-shaped is reported as unparsed
- **WHEN** a task's Covers references a critical-statement identifier that appears in `design.md` but not at the start of a line followed by a dash (for example, wrapped in bullet or bold markup)
- **THEN** `keel gate task-start` fails with a message reporting the identifier as unparsed and stating the required line shape

#### Scenario: A correctly-shaped identifier still resolves
- **WHEN** a task's Covers references a critical-statement identifier that appears exactly once at the start of a `design.md` line followed by a dash
- **THEN** `keel gate task-start` resolves the reference as authority, unchanged from today
