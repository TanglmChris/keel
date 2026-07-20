## ADDED Requirements

### Requirement: Accepted Review Status vocabulary is single-sourced and includes `done`

Keel MUST define the accepted Review `Status` vocabulary once as a single shared
constant consumed by both the completion gate and the context "already reviewed"
probe, and that vocabulary MUST include `done` alongside the existing passing
tokens. The two consumers MUST NOT maintain independent copies of the accepted
set.

#### Scenario: Gate and context share one accepted set

- **WHEN** the completion gate and the context already-reviewed probe each evaluate a Review `Status`
- **THEN** both derive the accepted set from the same shared constant
- **AND THEN** a `Status` token accepted by one is accepted by the other

#### Scenario: `done` completes on the Status axis

- **WHEN** a task presented to `task-complete` records Review `Status: done` with otherwise complete evidence
- **THEN** the gate treats the Review as passing on the Status axis
- **AND THEN** completion is not blocked solely because the token is `done` rather than `pass`

### Requirement: Gate rejections for validated forms name the field and accepted forms

When a completion or close gate rejects a hard-validated form — the Review
`Status` vocabulary, the Findings ownership shape, or the `## Expectation
Coverage` section — the resulting error MUST name the failing field or section
and MUST show the accepted forms or a minimal format sample, so an author can
repair from the message without reading validator source.

#### Scenario: Status rejection names the field and lists accepted tokens

- **WHEN** `task-complete` produces `semantic-review` because the Review `Status` is outside the accepted set
- **THEN** the error names the `Status` field and lists the accepted tokens, including `done`

#### Scenario: Findings rejection shows the accepted ownership forms

- **WHEN** `task-complete` produces `finding-owner` because a non-`none` Findings value has no durable owner
- **THEN** the error names the `Findings` field and shows the accepted forms: a `discard reason:`/`discard rationale:` prefix, a `keel/archive/…` path, or an existing `openspec/changes/<change>/…` artifact
- **AND THEN** the error states that `keel/HANDOFF.md` is not an accepted owner

#### Scenario: Expectation Coverage rejection carries a format sample

- **WHEN** `change-close` produces `expectation-coverage` because the section is missing or declares no `E<n>` closure
- **THEN** the error names the `## Expectation Coverage` section and carries a minimal `- E<n>: … Covered by: <task ids>` format sample
