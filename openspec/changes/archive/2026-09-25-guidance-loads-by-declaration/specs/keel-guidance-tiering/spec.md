# keel-guidance-tiering

## ADDED Requirements

### Requirement: A skill's stepwise guidance is referenced, not resident

Guidance that tells an executor *how* to carry out a skill SHALL live in `guidance.md` beside the
skill's `SKILL.md` rather than inside it, and the body SHALL name that file where the guidance was.
The body keeps every criterion.

#### Scenario: The body points at the guidance it moved

- **WHEN** a skill's `SKILL.md` has a `guidance.md` beside it
- **THEN** the body references that file by name
- **AND** the reference states the condition under which it is read

#### Scenario: A guidance file carries no criterion

- **WHEN** a `guidance.md` beside a skill body is read
- **THEN** it contains none of the vocabulary Keel states criteria in
- **AND** a guidance file that states a criterion is refused, naming the file and the word

### Requirement: The skip is declared by the repository

A repository MAY declare `executor_tier:` in `keel/config.yaml` as `standard` or `high`. A split
skill SHALL read its `guidance.md` unless the repository declares `high`. An absent declaration means
`standard`, and a value Keel cannot read fails closed to `standard`.

#### Scenario: An absent declaration reads the guidance

- **WHEN** no `executor_tier:` is declared
- **THEN** the reported tier is `standard`
- **AND** the skill's instruction to read its guidance is unconditional

#### Scenario: An unreadable value fails closed

- **WHEN** `executor_tier:` names a value outside the accepted set
- **THEN** the reported tier is `standard`
- **AND** the surface names the rejected value and the accepted ones

### Requirement: The tier is visible where the session starts

`keel context` and `keel --doctor` SHALL report the declared executor tier, and SHALL state that it
affects guidance only and changes no gate, criterion, evidence requirement, or Review.

#### Scenario: The projection reports the tier and its limit

- **WHEN** `keel context` runs in a repository declaring `executor_tier: high`
- **THEN** the projection reports the tier
- **AND** it states that guidance is all the tier affects
