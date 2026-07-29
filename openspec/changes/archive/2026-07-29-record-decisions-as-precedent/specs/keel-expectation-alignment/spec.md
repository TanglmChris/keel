## MODIFIED Requirements

### Requirement: Repository facts are inspected before user questions
Keel MUST inspect relevant code, tests, docs, OpenSpec artifacts, issues, and verified runtime behavior before asking the user to answer discoverable factual questions. It MUST distinguish F<n> facts from user-owned product decisions. Where a precedent store is declared, Keel MUST also consult the matching precedent before escalating a decision, and MUST record a new precedent when the user makes a decision the store does not yet cover.

#### Scenario: Repository answers the question
- **WHEN** current authoritative artifacts establish existing behavior, compatibility, command shape, or constraints
- **THEN** the agent records the fact with its basis
- **AND THEN** it asks the user only if a product choice remains after the fact is known

#### Scenario: Sources conflict
- **WHEN** code, tests, docs, and user wording disagree on an acceptance-relevant fact
- **THEN** Keel surfaces the contradiction and asks who or what has authority
- **AND THEN** specs do not silently choose one source

#### Scenario: A matching precedent is consulted before escalating
- **WHEN** a decision would be escalated to the user and a matching precedent exists in the declared store
- **THEN** the agent reads that precedent and its rationale before asking
- **AND THEN** an `authorized` precedent supplies the answer with a citation, while a `recorded` one supplies a recommendation and the question is still asked

#### Scenario: A new decision is recorded as a precedent
- **WHEN** the user makes a decision the declared store does not cover
- **THEN** the agent records it as a `recorded` precedent carrying its category, the decision, and the reasoning the user gave or confirmed
- **AND THEN** the reasoning is captured rather than the conclusion alone, because only the reasoning transfers to a decision not yet seen

#### Scenario: No store leaves alignment unchanged
- **WHEN** no precedent store is declared
- **THEN** alignment escalates and records exactly as it does without this capability
- **AND THEN** no prompt demands that a store be created
