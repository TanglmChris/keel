## MODIFIED Requirements

### Requirement: Keel supports pluggable domain lenses

Keel MUST treat domain alignment knowledge as pluggable lenses authored by the user in `keel/lenses/*.md`, not as content bundled inside `align-expectations`. The core MUST keep the on-demand mechanism (detect a domain signal, load the one matching lens, feed alignment/execution/review) without hardcoding any domain list. Each lens MUST be self-describing through an `Applies when:` header that names its domain signals. Keel MUST NOT require profile selection state or a `--profile` flag.

#### Scenario: Lenses are user-authored and self-describing

- **WHEN** a repo defines a lens at `keel/lenses/<name>.md`
- **THEN** the lens declares an `Applies when:` header naming the domain signals it covers
- **AND THEN** the core carries no built-in domain list that must match the lens

#### Scenario: Relevant lens loads on demand

- **WHEN** alignment detects a domain signal for which a matching `keel/lenses/` lens exists
- **THEN** it reads the lens whose `Applies when` matches
- **AND THEN** no rule keeps it from reading another lens it judges relevant

#### Scenario: No lens is a valid state

- **WHEN** a change shows a domain signal but the repo defines no matching lens
- **THEN** alignment, execution, and review proceed on the domain-agnostic path
- **AND THEN** no prompt demands a lens or a domain selection

### Requirement: Domain lenses serve execution and review phases

The execution and review skills (`tdd-or-test-first`, `debug-failure`, `review-checklist`) MUST consult the matching lens from `keel/lenses/` on demand when the change's artifacts or task scope signal that domain, and MUST NOT load any lens for changes without a matching signal.

#### Scenario: Domain-signaling change consults one lens

- **WHEN** a task's change artifacts or Touch scope signal exactly one domain during execution or review, and a matching lens exists in `keel/lenses/`
- **THEN** the consuming skill consults that lens before finalizing strategy, diagnosis, or review conclusions

#### Scenario: No signal loads nothing

- **WHEN** a change shows no domain signal
- **THEN** execution and review proceed without loading any lens
- **AND THEN** no prompt demands a domain selection

#### Scenario: Lenses carry phase-appropriate checks

- **WHEN** a lens is consulted during execution or review
- **THEN** it provides that domain's verification pitfalls, evidence expectations, and review checks under an `Execution and review checks` heading
