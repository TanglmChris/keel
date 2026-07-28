## MODIFIED Requirements

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
- **THEN** the error names the `Findings` field and shows the accepted forms: a `discard reason:`/`discard rationale:` prefix, a `keel/archive/…` path, an existing `openspec/changes/<change>/…` artifact, any other repo-relative path that exists, or an absolute `http`/`https` tracker reference
- **AND THEN** the error states that `keel/HANDOFF.md` is not an accepted owner

#### Scenario: Expectation Coverage rejection carries a format sample

- **WHEN** `change-close` produces `expectation-coverage` because the section is missing or declares no `E<n>` closure
- **THEN** the error names the `## Expectation Coverage` section and carries a minimal `- E<n>: … Covered by: <task ids>` format sample
