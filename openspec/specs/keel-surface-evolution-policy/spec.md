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

### Requirement: Native target capability is not a Keel design goal

Keel MUST NOT implement, wrap, or re-specify a capability the target runtime already provides natively, and MUST NOT define a surface that conflicts with one. Where a capability is native, Keel's scope is limited to declaring policy about its use — what is authorized, under what precondition, and what its result may settle — and the capability itself MUST remain the host's to perform.

#### Scenario: A native capability is declared about, not rebuilt

- **WHEN** a proposed Keel surface would perform something a target runtime already performs natively
- **THEN** the proposal is reduced to the policy Keel can declare about it, and the performing is left to the host
- **AND THEN** the design records which part was native and which part was Keel's, so a later reader can check the boundary rather than re-derive it

#### Scenario: A duplicate carrier is refused

- **WHEN** a proposed contract, brief, or projection would carry to the host something the host's own interface already carries
- **THEN** Keel extends the projection it already publishes instead of introducing a second carrier beside the native one
- **AND THEN** the refusal is recorded as a decision rather than left as an unexplained absence

#### Scenario: A conflicting surface is not shipped

- **WHEN** a proposed Keel surface would contradict a target's native behavior rather than merely repeat it
- **THEN** Keel does not ship it, because a target whose runtime and protocol disagree leaves the agent no correct action
- **AND THEN** the conflict returns to authoring instead of being resolved by precedence wording

#### Scenario: The thinnest surviving layer is named

- **WHEN** a change keeps a layer whose value over the native capability is narrow
- **THEN** the design names it as the surface most exposed to this requirement and records the argument for keeping it
- **AND THEN** that layer is the first candidate for removal when the argument stops holding
