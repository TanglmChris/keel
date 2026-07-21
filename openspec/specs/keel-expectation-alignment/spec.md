## Purpose

Define Keel's risk-scaled pre-spec and pre-task alignment of explicit and implicit requirements, non-goals, observable acceptance, evidence, and decision authority.

## Requirements

### Requirement: Keel aligns expectations before specs and executable tasks finalize
Keel MUST establish durable authority for explicit requirements, candidate implicit expectations, non-goals, observable acceptance, evidence expectations, constraints, and material decision boundaries before OpenSpec specs and executable tasks are finalized.

#### Scenario: Complete request uses the quick path
- **WHEN** the user's request, repository facts, and intended observable outcome are coherent and no material choice is unresolved
- **THEN** Keel states the extracted goals, non-goals, Acceptance, constraints, and evidence compactly
- **AND THEN** authoring may proceed without forcing an interactive interview

#### Scenario: Material ambiguity uses the deep path
- **WHEN** a choice can materially change user-visible behavior, external interface, acceptance, security/privacy/permission, data migration, protocol/state/timing/reset, generated equivalence, irreversible cost, dependency, or architecture
- **THEN** Keel pauses spec/task finalization and asks one decision at a time
- **AND THEN** each question explains why it matters and provides a recommended answer

#### Scenario: Missing authority blocks executable tasks
- **WHEN** a material product choice or acceptance boundary remains neither accepted, verified, durably owned, nor explicitly discarded
- **THEN** no affected task becomes executable
- **AND THEN** the uncertainty is recorded as Q<n> with an owner or resolution gate

### Requirement: Implicit expectations remain proposals until authorized
Keel MUST distinguish inferred candidate expectations from accepted user intent or verified repository facts. It MUST NOT turn user silence or model confidence into authority for a material product decision.

#### Scenario: Agent identifies a likely expectation
- **WHEN** the agent infers accessibility, compatibility, failure behavior, migration, performance, security, or other unstated expectations that affect completion
- **THEN** it labels them as candidates and explains their impact
- **AND THEN** material candidates require user acceptance or verified durable authority before entering specs

#### Scenario: Non-material assumption is reversible
- **WHEN** an implementation detail is low-risk, reversible, and does not alter observable acceptance or an execution boundary
- **THEN** the agent may state the assumption and proceed through the quick path
- **AND THEN** it does not burden the user with a decision that repository evidence can settle

### Requirement: Repository facts are inspected before user questions
Keel MUST inspect relevant code, tests, docs, OpenSpec artifacts, issues, and verified runtime behavior before asking the user to answer discoverable factual questions. It MUST distinguish F<n> facts from user-owned product decisions.

#### Scenario: Repository answers the question
- **WHEN** current authoritative artifacts establish existing behavior, compatibility, command shape, or constraints
- **THEN** the agent records the fact with its basis
- **AND THEN** it asks the user only if a product choice remains after the fact is known

#### Scenario: Sources conflict
- **WHEN** code, tests, docs, and user wording disagree on an acceptance-relevant fact
- **THEN** Keel surfaces the contradiction and asks who or what has authority
- **AND THEN** specs do not silently choose one source

### Requirement: Accepted alignment writes back to existing OpenSpec owners
Keel MUST route accepted alignment outcomes into proposal, design, specs, and tasks according to their durable ownership and MUST NOT create a separate alignment ledger, depend on chat history, or store detail in HANDOFF.

#### Scenario: Scope and non-goals are accepted
- **WHEN** alignment establishes motivation, scope, goals, or non-goals
- **THEN** proposal.md records them before downstream artifacts finalize

#### Scenario: Decisions and assumptions are accepted
- **WHEN** alignment resolves a material decision, fact, assumption, risk, or question
- **THEN** design.md records the applicable D/F/A/Q statement and basis

#### Scenario: Observable behavior is accepted
- **WHEN** alignment resolves user-visible positive, negative, edge, or failure behavior
- **THEN** specs record it as requirements and scenarios
- **AND THEN** tasks reference that authority through Covers and verification rather than duplicating chat prose

### Requirement: Alignment triggering is validated with realistic evidence
The alignment skill MUST have portable trigger metadata and MUST be validated with realistic positive triggers, negative triggers, artifact write-back checks, and real-task forward evidence before replacing the current authoring workflow.

#### Scenario: Positive trigger exposes consequential ambiguity
- **WHEN** a realistic request hides an acceptance-relevant material choice
- **THEN** the skill activates and resolves or durably owns that choice before specs/tasks finalize

#### Scenario: Negative trigger stays out of routine work
- **WHEN** a request is a clear local implementation task, unrelated conversation, or a factual question answered by the repository
- **THEN** the skill does not start a product interview or mutate OpenSpec artifacts

#### Scenario: Real-task evidence is independent
- **WHEN** the skill is forward-tested on generic, web/API, and hardware/generated-artifact cases
- **THEN** the evaluator receives raw task-local prompts and artifacts rather than intended answers or reviewer conclusions
- **AND THEN** evidence records trigger quality, question materiality, Acceptance quality, and durable write-back

### Requirement: Alignment skill content has reviewed provenance
Keel MUST identify the authoritative source, license implications, positive/negative trigger cases, and required real-task evidence for the new or materially expanded alignment skill and domain lenses.

#### Scenario: Keel-authored consolidation uses local authority
- **WHEN** existing Keel grill and lens guidance is consolidated
- **THEN** design or task evidence names the local canonical sources and repository package policy
- **AND THEN** target metadata remains additive rather than replacing portable SKILL.md authority

#### Scenario: External material is considered
- **WHEN** implementation proposes copying or materially adapting external skill or domain content
- **THEN** it records source, license, inclusion rationale, and required notice before inclusion
- **AND THEN** unresolved provenance blocks that content from the skill
