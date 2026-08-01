## ADDED Requirements

### Requirement: Semantic review checks the content a gate can only shape-check

Where a deterministic gate validates the form of a reference or a message but cannot reach its
content, the semantic review layer MUST make that check, and Keel MUST NOT move it into a gate.

A durable owner declared as a URL MUST already carry the content it claims to hold at the moment it
is cited. A failure message MUST name the actual cause of the failure it reports.

#### Scenario: A URL owner is checked for content at citation time

- **WHEN** an entry closes with a `Durable owner:` naming an absolute URL
- **THEN** semantic review confirms the referenced location already carries the content the entry claims it holds
- **AND THEN** an empty or absent target returns the work to create that content before the reference stands, rather than deferring the check to archive

#### Scenario: A failure message is checked against its actual cause

- **WHEN** one condition guards two distinct failure modes and reports a single message
- **THEN** semantic review requires the condition to be split so each failure reports its own cause
- **AND THEN** a message naming a cause that is not the cause is treated as a defect, because it sends a reader to a place with no problem in it

#### Scenario: Neither check migrates into a deterministic gate

- **WHEN** a change proposes to enforce either check in `task-start`, `task-complete`, or `change-close`
- **THEN** it is refused
- **AND THEN** the reason is that fetching a reference would make a gate non-local and non-offline, and judging whether a message misleads would require a model — the properties gates exist to avoid depending on

#### Scenario: Neither check judges quality

- **WHEN** semantic review evaluates a rationale it cannot assess, or wording it would have phrased differently
- **THEN** the checks concern only whether the content is present and whether the stated cause is the real one
- **AND THEN** no review outcome claims Keel judged the reasoning
