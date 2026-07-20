## ADDED Requirements

### Requirement: Gate-validated forms are expressed in the author-facing surface

Every form that a completion or close gate hard-validates MUST be expressed in
the author-facing surface an author reads — the `keel-spec-driven` tasks template
and the `tasks` artifact authoring instruction — not only in the validators. An
author who follows the shipped template and instruction MUST NOT hit an avoidable
completion or close hard-stop over a form the surface never described.

#### Scenario: Accepted Review Status tokens are documented for authors

- **WHEN** an author consults the `keel-spec-driven` tasks template or its `tasks` artifact instruction
- **THEN** the accepted Review `Status` tokens are enumerated there, including `done`
- **AND THEN** the author can record a passing Status without reading gate source

#### Scenario: Accepted Findings forms are documented for authors

- **WHEN** an author consults the tasks template or the `tasks` artifact instruction
- **THEN** the accepted Findings forms are enumerated: `none`, or a recorded finding carrying a durable owner — a `discard reason:`/`discard rationale:` prefix, a `keel/archive/…` path, or an existing `openspec/changes/…` artifact
- **AND THEN** the surface states that an observation worth recording must take one of these owned forms rather than a bare note, so it does not fail `finding-owner`

#### Scenario: Expectation Coverage section ships in the template

- **WHEN** an author starts a change from the `keel-spec-driven` tasks template
- **THEN** the template already contains a `## Expectation Coverage` section carrying a `- None.` default and an `- E<n>: … Covered by: <task ids>` example
- **AND THEN** the `tasks` artifact instruction requires and formats that section so `change-close` finds it rather than the author discovering the requirement only at close
