## ADDED Requirements

### Requirement: The published spec store is validated by the tool Keel ships

Validation MUST run the OpenSpec validator over the repository's own published spec store in strict mode and MUST fail naming each spec that did not pass, because the store is the artifact Keel asks every consumer to trust and no other check reads it. Validating a change validates the change; it says nothing about the specs the change was promoted into.

The assertion MUST be that no published spec fails. A tolerated failure count MUST NOT be recorded in place of it, since a recorded tolerance is a budget and a budget for failures is where the next one hides.

The check MUST state the validator version it exercised, so a result is attributable to the program that produced it, and MUST report a skip rather than a pass when no validator resolves.

#### Scenario: A published spec that fails strict validation fails the suite
- **WHEN** validation runs and a spec in the published store does not pass strict validation
- **THEN** the suite fails naming that spec
- **AND THEN** the failure is not absorbed into a recorded count of known failures

#### Scenario: The store is asserted rather than a change
- **WHEN** validation covers strict spec validation
- **THEN** the assertion reads the published spec store
- **AND THEN** validating a change is not accepted as coverage of the store

#### Scenario: The validator that answered is named
- **WHEN** the strict store validation reports its result
- **THEN** it states the validator version it exercised

#### Scenario: No validator resolves
- **WHEN** no OpenSpec validator can be resolved
- **THEN** the scenario reports the skip rather than passing silently
