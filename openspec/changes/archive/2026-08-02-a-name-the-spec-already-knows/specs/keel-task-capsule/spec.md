## ADDED Requirements

### Requirement: An unresolved reference into an existing capability names what failed
When a `Covers` reference does not resolve, Keel MUST report which segment failed rather than the reference alone. When the reference's second segment names no Requirement but does name a Scenario the capability declares, the diagnostic MUST name the Requirement that Scenario belongs to and MUST state the corrected `capability / requirement / scenario` reference. When the capability declares no spec at all, the diagnostic MUST say so rather than describing the name inside it. Reporting what a spec contains is not heuristic matching: the reference still fails, with the same diagnostic code, and Keel MUST NOT resolve it to a near match.

#### Scenario: A Scenario offered as a Requirement is named as one
- **WHEN** a `Covers` reference's second segment names a Scenario the capability declares rather than a Requirement
- **THEN** the `unresolved-covers` diagnostic names the Requirement that Scenario sits under and states the corrected three-segment reference
- **AND THEN** the reference is still refused

#### Scenario: A name the spec does not declare is reported as read
- **WHEN** a `Covers` reference names an existing capability whose spec declares neither that Requirement nor a Scenario by that name
- **THEN** the diagnostic states that the capability's spec was read and holds no such name, and states the hierarchy
- **AND THEN** the reference is still refused

#### Scenario: A capability with no spec is distinguished from a name that is absent
- **WHEN** a `Covers` reference's first segment names a capability for which no spec exists
- **THEN** the diagnostic states that no spec declares that capability
- **AND THEN** it does not describe the remaining segments as the cause

#### Scenario: A Scenario declared under more than one Requirement offers no correction
- **WHEN** the named Scenario appears under more than one Requirement of the capability
- **THEN** the diagnostic names the Requirements it appears under
- **AND THEN** it states no single corrected reference

#### Scenario: What resolves is unchanged
- **WHEN** a `Covers` reference resolves to a Requirement or Scenario
- **THEN** it compiles to the same authority, source, and Acceptance as before
- **AND THEN** no diagnostic is added to a reference that resolves
