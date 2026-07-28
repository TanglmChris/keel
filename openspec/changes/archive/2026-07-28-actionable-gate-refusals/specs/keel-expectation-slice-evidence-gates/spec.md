## ADDED Requirements

### Requirement: A durable owner may be any file the repository keeps, and a refusal names what it accepts

The accepted durable-owner forms are shape checks. A gate runs without network
and cannot confirm that a URL resolves or that an archive path is the right one,
so a whitelist of prefixes verifies nothing beyond spelling. A repo-relative path
is the one form a gate can actually check, and refusing it while accepting the
unverifiable ones inverts the rigour.

A `Durable owner:` MUST therefore be accepted when it names a repo-relative path
that exists in the repository the gate is running against, in addition to the
forms already accepted. A path that does not exist MUST be refused, which is a
check the prefix whitelist could not make. `keel/HANDOFF.md` MUST stay refused
even though it exists, because the protocol defines it as a pointer override
rather than an owner: existence is necessary, not sufficient.

The same vocabulary MUST apply wherever a durable owner closes an entry —
Review `Findings`, `## Expectation Coverage`, and `## Invalidates` — so a form
accepted in one place is never refused in another. Every refusal of an owner or
a closure MUST state the forms it would accept, because an author who cannot
see the boundary can only find it by trial.

#### Scenario: A repo ledger is a legitimate owner

- **WHEN** an entry closes with a `Durable owner:` naming a repo-relative file that exists
- **THEN** the gate accepts it
- **AND THEN** the same path is accepted whether it closes an invalidation, an expectation, or a review finding

#### Scenario: An owner that does not exist is refused

- **WHEN** a `Durable owner:` names a repo-relative path with no file behind it
- **THEN** the gate refuses the entry and says the path does not exist
- **AND THEN** the refusal is distinguishable from an entry that named no owner at all

#### Scenario: The pointer override is still not an owner

- **WHEN** a `Durable owner:` names `keel/HANDOFF.md`
- **THEN** the gate refuses it even though the file exists
- **AND THEN** the refusal states that this file is a pointer override rather than a durable owner

#### Scenario: A refusal states the accepted forms

- **WHEN** a gate refuses an entry for lacking a closure or a valid owner
- **THEN** the diagnostic names the forms it accepts, including the existing-path form
- **AND THEN** the author does not have to discover the boundary by trying candidates

## MODIFIED Requirements

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
- **THEN** the accepted Findings forms are enumerated: `none`, or a recorded finding carrying a durable owner — a `discard reason:`/`discard rationale:` prefix, a `keel/archive/…` path, an existing `openspec/changes/…` artifact, or any other repo-relative path that exists
- **AND THEN** the surface states that an observation worth recording must take one of these owned forms rather than a bare note, so it does not fail `finding-owner`

#### Scenario: Expectation Coverage section ships in the template

- **WHEN** an author starts a change from the `keel-spec-driven` tasks template
- **THEN** the template already contains a `## Expectation Coverage` section carrying a `- None.` default and an `- E<n>: … Covered by: <task ids>` example
- **AND THEN** the `tasks` artifact instruction requires and formats that section so `change-close` finds it rather than the author discovering the requirement only at close
