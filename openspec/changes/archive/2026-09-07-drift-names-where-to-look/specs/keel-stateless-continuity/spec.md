## ADDED Requirements

### Requirement: A reported drift names where the covered authority was read from

When Keel reports a task contract fingerprint drift, it MUST name the authority sources the
capsule resolved its text from, and MUST state that Evidence, Review, and the task checkbox are
not covered by the fingerprint.

Keel MUST continue to report both the recorded and the current fingerprint. Naming the sources
MUST NOT change what the fingerprint covers, when drift is detected, or that drift blocks.

Keel MUST NOT claim which field moved, because the previous capsule is not retained and only its
digest is.

#### Scenario: Drift names its authority sources

- **WHEN** a task's recorded fingerprint differs from the capsule compiled now
- **THEN** the report names each distinct source the capsule resolved authority text from
- **AND THEN** it reports both fingerprints as before

#### Scenario: Drift says what it does not cover

- **WHEN** a drift is reported
- **THEN** the report states that Evidence, Review, and the checkbox do not move the fingerprint

#### Scenario: Drift does not guess

- **WHEN** a drift is reported
- **THEN** the report does not name a field or statement as the one that changed
