## ADDED Requirements

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
