## ADDED Requirements

### Requirement: A re-record may carry what the author declares survived it

`keel gate task-start --record` MUST accept a declaration naming the checks whose evidence the
author states the contract change did not affect.

When a re-record lands a different fingerprint, Keel MUST report which checks remain stale and,
when a declaration is given, which were declared unaffected and that the narrowing came from that
declaration. Keel MUST NOT report the declared checks as stale.

Keel MUST refuse a declaration naming anything that is not a check of the compiled contract, and
MUST refuse a declaration given without a re-record.

Keel MUST NOT verify that the declaration is true, and MUST NOT present it as verified: it does not
retain the previous capsule and cannot compare a check's former text to its current one. The
declaration MUST NOT change what completion requires.

#### Scenario: The warning names only what is still stale

- **WHEN** a re-record lands a different fingerprint and the author declares two of three checks unaffected
- **THEN** the report names the remaining check as stale
- **AND THEN** it names the declared checks and attributes the narrowing to the declaration

#### Scenario: A declaration names a check that does not exist

- **WHEN** a declaration names something the compiled contract does not declare as a check
- **THEN** `task-start` refuses it

#### Scenario: A declaration without a re-record is refused

- **WHEN** a declaration is given without a re-record
- **THEN** `task-start` refuses it

#### Scenario: Completion is unchanged

- **WHEN** a task completes after a declaration was made
- **THEN** every `M<n>` still requires its own Evidence, red-green still applies, and the semantic Review still runs
