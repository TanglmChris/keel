## ADDED Requirements

### Requirement: A quoted disposition marker is not a disposition

When Keel reads `Review Findings` for a finding's disposition, a marker written inside an
inline-code span MUST NOT be read as a disposition. This applies to every disposition marker
Keel recognizes, not only to the one a given refusal names.

A quoted marker MUST NOT change what the real dispositions in the same field report. In
particular, Keel MUST NOT report a block as carrying a resolution with unusable evidence when
the only resolution marker in it is quoted.

When Keel refuses a resolution because its evidence is unusable, the refusal MUST name what
Keel read as that evidence.

#### Scenario: A finding discusses the marker and owns its finding

- **WHEN** a Findings block names a disposition marker inside inline code and records a genuine `Durable owner:` reference
- **THEN** `task-complete` accepts the block
- **AND THEN** it reports no resolution-evidence problem

#### Scenario: A quoted marker does not eclipse a real one

- **WHEN** a Findings block names a disposition marker inside inline code and also records a real resolution naming a check the task declares
- **THEN** `task-complete` accepts the block

#### Scenario: A block whose only marker is quoted has no disposition

- **WHEN** a Findings block's only disposition marker is inside inline code
- **THEN** `task-complete` refuses it as carrying no disposition
- **AND THEN** it does not refuse it as a resolution whose evidence is unusable

#### Scenario: The refusal names what was read

- **WHEN** a resolution's evidence is neither a declared check nor a path that exists
- **THEN** the refusal names the text Keel read as that evidence
