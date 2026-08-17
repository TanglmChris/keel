## MODIFIED Requirements

### Requirement: Unresolved critical-statement Covers references distinguish missing from unparsed
Keel MUST report a `D<n>`/`F<n>`/`A<n>`/`Q<n>` Covers reference that fails to resolve against `design.md` as missing when the identifier is textually absent from the file, and as unparsed — naming the accepted line shapes — when the identifier is present in the file but in none of them.

#### Scenario: Identifier absent from design.md is reported as missing
- **WHEN** a task's Covers references a critical-statement identifier that does not appear anywhere in the change's `design.md`
- **THEN** `keel gate task-start` fails with a message reporting the identifier as missing

#### Scenario: Identifier present but mis-shaped is reported as unparsed
- **WHEN** a task's Covers references a critical-statement identifier that appears in `design.md` but in none of the accepted line shapes (for example, in a heading, followed by a colon instead of a dash, or mentioned mid-line)
- **THEN** `keel gate task-start` fails with a message reporting the identifier as unparsed and naming the accepted line shapes

#### Scenario: A correctly-shaped identifier still resolves
- **WHEN** a task's Covers references a critical-statement identifier whose `design.md` line matches exactly one accepted shape
- **THEN** `keel gate task-start` resolves the reference as authority

## ADDED Requirements

### Requirement: Critical-statement lines are accepted in the shapes authors write
Keel MUST resolve a `design.md` critical-statement line whose identifier opens the line bare, wrapped in balanced `**`, after a CommonMark list bullet (`-`, `*`, or `+`), or both, followed by a dash and the statement. Keel MUST still fail a reference matching more than one line — in any mix of accepted shapes — as duplicated rather than picking one.

#### Scenario: A bulleted critical statement resolves
- **WHEN** a task's Covers references an identifier whose `design.md` line reads `- D2 — statement`
- **THEN** `keel gate task-start` resolves the reference as authority with the statement text

#### Scenario: A bold critical statement resolves
- **WHEN** a task's Covers references an identifier whose `design.md` line reads `**D2** — statement`
- **THEN** `keel gate task-start` resolves the reference as authority with the statement text

#### Scenario: A bulleted bold critical statement resolves
- **WHEN** a task's Covers references an identifier whose `design.md` line reads `- **D2** — statement`
- **THEN** `keel gate task-start` resolves the reference as authority with the statement text

#### Scenario: A bare critical statement still resolves
- **WHEN** a task's Covers references an identifier whose `design.md` line reads `D2 — statement`
- **THEN** `keel gate task-start` resolves the reference as authority, unchanged from before the shapes widened

#### Scenario: The same identifier in two shapes is duplicated
- **WHEN** a task's Covers references an identifier that matches two `design.md` lines, one bare and one bulleted or bold
- **THEN** `keel gate task-start` fails the reference as duplicated
