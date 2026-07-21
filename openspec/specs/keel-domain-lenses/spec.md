## Purpose

Define Keel's pluggable domain lenses — how user-authored lenses in `keel/lenses/` are scaffolded, loaded on demand, and diagnosed — and the deliberate retirement of the v3 domain profiles they replace.
## Requirements
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
- **THEN** Keel reports that domain guidance is now user-authored lenses in `keel/lenses/*.md` and the flag is no longer supported
- **AND THEN** it does not silently create target-specific profile state

### Requirement: Keel supports pluggable domain lenses

Keel MUST treat domain alignment knowledge as pluggable lenses authored by the user in `keel/lenses/*.md`, not as content bundled inside `keel-align-expectations`. The core MUST keep the on-demand mechanism (detect a domain signal, load the one matching lens, feed alignment/execution/review) without hardcoding any domain list. Each lens MUST be self-describing through an `Applies when:` header that names its domain signals. Keel MUST NOT require profile selection state or a `--profile` flag.

#### Scenario: Lenses are user-authored and self-describing

- **WHEN** a repo defines a lens at `keel/lenses/<name>.md`
- **THEN** the lens declares an `Applies when:` header naming the domain signals it covers
- **AND THEN** the core carries no built-in domain list that must match the lens

#### Scenario: Relevant lens loads on demand

- **WHEN** alignment detects a domain signal for which a matching `keel/lenses/` lens exists
- **THEN** it reads only the lens whose `Applies when` matches
- **AND THEN** unrelated lenses do not enter context

#### Scenario: No lens is a valid state

- **WHEN** a change shows a domain signal but the repo defines no matching lens
- **THEN** alignment, execution, and review proceed on the domain-agnostic path
- **AND THEN** no prompt demands a lens or a domain selection

### Requirement: Domain lenses serve execution and review phases

The execution and review skills (`keel-tdd-or-test-first`, `keel-debug-failure`, `keel-review-checklist`) MUST consult the single matching lens from `keel/lenses/` on demand when the change's artifacts or task scope signal that domain, and MUST NOT load any lens for changes without a matching signal.

#### Scenario: Domain-signaling change consults one lens

- **WHEN** a task's change artifacts or Touch scope signal exactly one domain during execution or review, and a matching lens exists in `keel/lenses/`
- **THEN** the consuming skill consults that one lens before finalizing strategy, diagnosis, or review conclusions
- **AND THEN** no other lens is loaded

#### Scenario: No signal loads nothing

- **WHEN** a change shows no domain signal
- **THEN** execution and review proceed without loading any lens
- **AND THEN** no prompt demands a domain selection

#### Scenario: Lenses carry phase-appropriate checks

- **WHEN** a lens is consulted during execution or review
- **THEN** it provides that domain's verification pitfalls, evidence expectations, and review checks under an `Execution and review checks` heading

### Requirement: Shipped lens templates stay single-source

Keel MUST ship the built-in domain lenses (`web`, `hardware`, `hardware-dsl`) as opt-in templates authored in exactly one canonical location under `assets/lenses/`. Every shipped copy of a template MUST be byte-identical to its canonical source, and validation MUST fail on divergence or size-budget overflow. User lenses in `keel/lenses/` are user-owned data and MUST NOT be policed by this single-source rule.

#### Scenario: Template projections are byte-identical

- **WHEN** the build ships lens templates into distribution surfaces
- **THEN** every shipped template copy is byte-identical to its `assets/lenses/` source
- **AND THEN** validation fails when any copy diverges

#### Scenario: Template size budget is enforced

- **WHEN** a lens template exceeds its declared size budget
- **THEN** validation fails naming the offending template
- **AND THEN** overflow depth is directed to dedicated skills per the Dedicated Skill Policy

#### Scenario: User lenses are not policed

- **WHEN** a user authors or edits a lens in `keel/lenses/`
- **THEN** validation does not require it to match any shipped template
- **AND THEN** the user lens is free to diverge in content and size

### Requirement: Keel diagnoses the domain lens surface

Keel check and doctor behavior MUST diagnose the shipped lens templates and the `keel lenses` scaffold path as one surface. It MUST NOT report installed or requested domain profiles as active capability state.

#### Scenario: Lens template set is complete

- **WHEN** doctor inspects a target
- **THEN** it reports the shipped lens templates as present or incomplete

#### Scenario: Legacy profile is discovered

- **WHEN** doctor finds a separately installed `keel-profile-*` skill from v3
- **THEN** it reports a migration warning without treating that skill as current state
- **AND THEN** it preserves user-modified bytes

### Requirement: Keel scaffolds domain lenses

Keel MUST provide a `keel lenses` command that lists shipped lens templates and lenses installed in the repo, and scaffolds a template into `keel/lenses/`. Scaffolding MUST NOT overwrite an existing user lens without an explicit force, and MUST NOT run automatically on `keel --init`.

#### Scenario: Listing available and installed lenses

- **WHEN** a user runs `keel lenses list`
- **THEN** Keel reports the shipped templates (`web`, `hardware`, `hardware-dsl`) and any lenses present in `keel/lenses/`

#### Scenario: Scaffolding a template

- **WHEN** a user runs `keel lenses add web`
- **THEN** Keel copies the `web` template into `keel/lenses/web.md`
- **AND THEN** the scaffolded lens carries its `Applies when:` header ready to edit

#### Scenario: Scaffolding does not clobber a user lens

- **WHEN** `keel lenses add <name>` targets a path that already exists in `keel/lenses/`
- **THEN** Keel refuses without an explicit force flag
- **AND THEN** the existing user lens is left untouched

