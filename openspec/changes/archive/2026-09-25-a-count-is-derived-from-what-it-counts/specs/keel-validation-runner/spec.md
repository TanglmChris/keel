## ADDED Requirements

### Requirement: An assertion about a set is derived from that set

Where the suite asserts that a document describes a set the code defines, it MUST read that set from
the code rather than restate it as a literal, and its failure MUST name the member that is missing
rather than a disagreement between two counts. A literal restatement has to be hand-edited whenever
the set changes, and the edit is discovered by a scenario whose name has nothing to do with what was
changed; a count is additionally lossy, because it tells an author that two numbers differ rather
than which line to write.

A prose count in the document MAY remain unasserted. Checking it would reintroduce the literal, and a
document that names every member while miscounting them misleads no reader about what the set
contains.

#### Scenario: A document missing a member fails, naming it
- **WHEN** the code defines a set member the document does not name
- **THEN** the check fails and the diagnostic names that member
- **AND THEN** the diagnostic does not report a count

#### Scenario: Adding a member costs only the document
- **WHEN** a member is added to the set the code defines and the document names it
- **THEN** the check passes with no edit to the check itself
- **AND THEN** no assertion elsewhere requires a hand-updated number
