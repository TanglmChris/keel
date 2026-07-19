## Purpose

Define optional Keel domain profiles and their explicit installation and diagnostic behavior.
## Requirements
### Requirement: Keel supports optional domain profiles
Keel v4 MUST preserve web, hardware, and hardware-DSL alignment knowledge as conditionally loaded references inside `keel-align-expectations`. It MUST NOT package those domains as separately installed first-class profile skills or require profile selection state.

#### Scenario: Domain references are packaged once
- **WHEN** Keel's canonical alignment skill is packaged for Codex or Claude
- **THEN** it includes `references/web.md`, `references/hardware.md`, and `references/hardware-dsl.md`
- **AND THEN** it does not generate separate `keel-profile-*` skills

#### Scenario: Relevant domain loads on demand
- **WHEN** alignment detects UI/API/routing/persistence, RTL/protocol/timing/reset, or hardware-DSL/generated-equivalence risk
- **THEN** it reads only the applicable domain reference or references
- **AND THEN** unrelated domain guidance does not enter context

#### Scenario: Default install needs no profile option
- **WHEN** Keel v4 is initialized or installed
- **THEN** domain references arrive with the alignment skill without `--profile`
- **AND THEN** users do not manage profile install state

### Requirement: Keel diagnoses domain profile surface
Keel v4 check and doctor behavior MUST diagnose the alignment skill and its required domain references as one surface. It MUST NOT report installed/requested domain profiles as active v4 capability state.

#### Scenario: Alignment reference set is complete
- **WHEN** doctor inspects a v4 target
- **THEN** it reports the canonical alignment skill and required reference set as present or incomplete

#### Scenario: Legacy profile is discovered
- **WHEN** doctor finds a separately installed `keel-profile-*` skill from v3
- **THEN** it reports a migration warning without treating that skill as current v4 state
- **AND THEN** it preserves user-modified bytes

### Requirement: Keel removes domain profiles deliberately
Keel v4 migration MUST remove packaged unmodified legacy profile skills and obsolete profile metadata/options conservatively while preserving user-modified legacy files with an explicit warning.

#### Scenario: Packaged legacy profile migrates
- **WHEN** update finds a legacy profile whose bytes match a packaged v3 version
- **THEN** it removes the redundant first-class profile after the alignment references are present
- **AND THEN** no HANDOFF or hidden state records the migration

#### Scenario: Modified legacy profile is preserved
- **WHEN** update finds a user-modified legacy profile
- **THEN** it leaves the file untouched and reports the path and manual migration choice
- **AND THEN** the v4 alignment reference remains canonical for new executions

#### Scenario: Obsolete profile flags are rejected clearly
- **WHEN** a v4 user invokes `--profile`
- **THEN** Keel reports that domain references are bundled and the flag is no longer supported
- **AND THEN** it does not silently create target-specific profile state

### Requirement: Domain references serve execution and review phases
The execution and review skills MUST consult the single matching domain reference on demand when the change's artifacts or task scope signal that domain, and MUST NOT load domain references for changes without a matching signal.

#### Scenario: Domain-signaling change consults one reference
- **WHEN** a task's change artifacts or Touch scope signal exactly one supported domain during execution or review
- **THEN** the consuming skill consults that one domain reference before finalizing strategy, diagnosis, or review conclusions
- **AND THEN** no other domain reference is loaded

#### Scenario: No signal loads nothing
- **WHEN** a change shows no supported domain signal
- **THEN** execution and review proceed without loading any domain reference
- **AND THEN** no prompt demands a domain selection

#### Scenario: References carry phase-appropriate checks
- **WHEN** a domain reference is consulted during execution or review
- **THEN** it provides that domain's verification pitfalls, evidence expectations, and review checks
- **AND THEN** the reference stays within its validated size budget

### Requirement: Domain reference authority stays single-source
Domain references MUST be authored in exactly one canonical location, every shipped or consuming copy MUST be byte-identical to the canonical source, and validation MUST fail on divergence or budget overflow.

#### Scenario: Projections are byte-identical
- **WHEN** the build projects domain references into shipped surfaces
- **THEN** every projected copy is byte-identical to the canonical source
- **AND THEN** validation fails when any copy diverges

#### Scenario: Size budget is enforced
- **WHEN** a domain reference exceeds its declared size budget
- **THEN** validation fails naming the offending reference
- **AND THEN** overflow depth is directed to dedicated skills per the Dedicated Skill Policy

