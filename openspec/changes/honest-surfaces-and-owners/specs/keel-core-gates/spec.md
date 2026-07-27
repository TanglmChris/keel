## MODIFIED Requirements

### Requirement: Semantic judgment remains agent-owned

Keel MUST NOT claim that deterministic gate structure proves product intent, behavioral test sufficiency, design quality, or risk completeness. Required semantic conclusions MUST be recorded by the current agent in task Review evidence. Wherever a durable follow-up owner is required, the accepted forms MUST include an external tracker reference alongside the repository-local forms.

#### Scenario: Completion Review is required
- **WHEN** a task is presented to `task-complete`
- **THEN** its Evidence contains Review `Status`, `Acceptance check`, `Scope check`, and `Findings`
- **AND THEN** a missing or non-passing required Review produces `needs-review`

#### Scenario: Findings require durable ownership
- **WHEN** Review identifies an unresolved finding
- **THEN** `task-complete` requires a durable OpenSpec task, new change, archive-evidence owner, absolute `http` or `https` tracker reference, or explicit discard rationale
- **AND THEN** `keel/HANDOFF.md` is not accepted as that owner

#### Scenario: An external tracker owns a finding without a local proxy file
- **WHEN** a Review `Findings` value or an `## Expectation Coverage` `Durable owner:` entry names an absolute `http` or `https` reference
- **THEN** the gate accepts it as a durable owner without requiring a repository-local file written only to satisfy the shape
- **AND THEN** both checks accept the tracker form, and every form either check accepted before is still accepted

#### Scenario: Gate does not reinterpret acceptance
- **WHEN** command Evidence and Review are present
- **THEN** Core validates their required shape and references
- **AND THEN** Core does not replace `keel-review-checklist` by independently judging whether the command proves Acceptance

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
- **THEN** the error names the `Findings` field and shows the accepted forms: a `discard reason:`/`discard rationale:` prefix, a `keel/archive/…` path, an existing `openspec/changes/<change>/…` artifact, or an absolute `http`/`https` tracker reference
- **AND THEN** the error states that `keel/HANDOFF.md` is not an accepted owner

#### Scenario: Expectation Coverage rejection carries a format sample

- **WHEN** `change-close` produces `expectation-coverage` because the section is missing or declares no `E<n>` closure
- **THEN** the error names the `## Expectation Coverage` section and carries a minimal `- E<n>: … Covered by: <task ids>` format sample
