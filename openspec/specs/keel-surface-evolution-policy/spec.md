# keel-surface-evolution-policy Specification

## Purpose
TBD - created by archiving change define-surface-evolution-evidence-policy. Update Purpose after archive.
## Requirements
### Requirement: Surface cede decisions are grounded in first-party coverage evidence

Keel MUST NOT cede a Keel-maintained target entry point to upstream generation, or retire an existing projection surface, without a durable first-party coverage report comparing the upstream-generated surface against every affected Keel-maintained entry point and naming the Keel deltas that must survive.

#### Scenario: Cede recommendation carries evidence
- **WHEN** a change proposes handing a Keel-maintained target surface to upstream OpenSpec generation
- **THEN** its authority includes a coverage report row for each affected entry point, sourced from installed CLI output or upstream first-party documentation
- **AND THEN** each row records the upstream equivalent as exists, partial, or none, plus the surviving Keel delta and a cede, keep, or wrap recommendation

#### Scenario: Missing coverage evidence blocks the cede change
- **WHEN** no first-party coverage report exists for an affected surface
- **THEN** no implementation change ceding or retiring that surface becomes executable
- **AND THEN** the missing evidence is recorded as the blocking gap

### Requirement: Host-native surface integrations require recorded design authority

Keel MUST NOT implement a new host-native surface integration (such as projecting task state onto a host task surface or admitting host review output as evidence) until its material design questions are resolved into recorded design decisions, and MUST route the resulting implementation authority to a change that carries the corresponding spec deltas.

#### Scenario: Design questions resolve before implementation
- **WHEN** a proposed host-native integration has open material questions about trigger, lifecycle, drift semantics, or evidence admissibility
- **THEN** each question is resolved into a recorded D-statement or the integration is explicitly declined
- **AND THEN** no implementation task for the integration becomes executable before that resolution

#### Scenario: Projection non-authority is preserved
- **WHEN** a host-native integration design is recorded
- **THEN** it keeps OpenSpec artifacts, Git, capsule fingerprints, and deterministic gates as the only durable authority
- **AND THEN** it introduces no scheduler, auto-advance, second writer of OpenSpec state, or session database

