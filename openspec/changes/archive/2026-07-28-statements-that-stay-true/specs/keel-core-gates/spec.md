## ADDED Requirements

### Requirement: A contract anchor is reverifiable while its change is live

A recorded fingerprint is described as recompiled and compared at resume,
projection, and completion. That guarantee holds while the change is live and
stops holding when it is archived: the compiled capsule records each authority's
`source` as a path under the change directory, and archiving renames that
directory, so an archived task recompiles to a different value. Nothing is
broken by this — an archived task is never resumed or completed — but an
unstated boundary reads as no boundary, and a reader who recompiles an archived
anchor to check it will conclude the contract drifted.

Keel MUST state that a contract anchor is reverifiable for as long as its change
is live, and becomes a historical record once the change is archived. Keel MUST
NOT claim or imply that an archived anchor can be recompiled to the value it
records.

#### Scenario: A live anchor recompiles to its recorded value

- **WHEN** a task of an active change is recompiled at resume, projection, or completion
- **THEN** its fingerprint equals the value recorded in its Evidence `Contract` line unless the contract genuinely changed
- **AND THEN** a difference is contract drift and hard-stops

#### Scenario: An archived anchor is a record, not an assertion

- **WHEN** a task under `openspec/changes/archive/` is recompiled
- **THEN** the difference from its recorded anchor is expected, because the change directory it names has been renamed
- **AND THEN** the documented guarantee does not claim otherwise, so the difference is not read as drift
