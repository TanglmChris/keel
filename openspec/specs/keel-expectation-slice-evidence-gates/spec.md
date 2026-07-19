## Purpose

Define Keel's lightweight expectation-to-slice-to-evidence gates for task execution alignment.

## Requirements

### Requirement: Keel defines critical expectations as execution authority

Keel MUST treat documented critical expectations as the authority for task execution alignment. A critical expectation is a documented statement that affects completion definition or execution boundaries.

#### Scenario: Critical expectations are durable
- **WHEN** an expectation affects completion definition or execution boundaries
- **THEN** Keel guidance requires it to be captured in OpenSpec artifacts, Keel protocol text, task evidence, or an explicit durable follow-up owner
- **AND THEN** Keel guidance does not require future agents to reconstruct that expectation from chat history

#### Scenario: Non-critical discussion does not become tracked state
- **WHEN** a discussion contains examples, undecided ideas, style preferences, or unaccepted agent proposals
- **THEN** Keel guidance does not require those items to be tracked as critical expectations unless they are accepted into durable artifacts

### Requirement: Task Authoring Gate covers critical expectations

Keel MUST define a Task Authoring Gate that checks whether critical expectations relevant to the change are covered by executable slices, deferred to durable owners, or explicitly discarded with rationale.

#### Scenario: Task authoring covers expectations
- **WHEN** tasks are authored for a Keel change
- **THEN** Keel guidance requires each relevant critical expectation to be covered by at least one task slice, deferred to a durable follow-up owner, or discarded with an explicit reason
- **AND THEN** the gate remains focused on expectation coverage rather than general code quality

#### Scenario: Complex changes may use an expectation map
- **WHEN** a change has enough critical expectations that lightweight references become ambiguous
- **THEN** Keel guidance allows the change to add an explicit Expectation Map or expectation IDs
- **AND THEN** Keel guidance does not require expectation IDs for ordinary changes

#### Scenario: Authoring gate covers hidden-knowledge assumptions
- **WHEN** authoring grill or a domain profile identifies accepted hidden-knowledge assumptions
- **THEN** Keel guidance treats those assumptions as critical expectations when they affect completion definition or execution boundaries
- **AND THEN** tasks must cover, defer, or discard them before the relevant slice can be selected

### Requirement: Slice Start Gate blocks incomplete current execution contracts
Keel MUST block implementation of the current selected slice or explicitly authorized contiguous slice group until the compiled capsule resolves a complete executable task contract. Compact source tasks MAY inherit versioned defaults and Acceptance from referenced OpenSpec authority; fields need not be duplicated literally when the capsule resolves them without guessing.

#### Scenario: Selected slice has executable capsule
- **WHEN** an agent selects a current slice for implementation
- **THEN** Keel requires its `Covers` entries to resolve the source expectations and observable Acceptance
- **AND THEN** the compiled capsule contains Read, Touch, mode, verification strategy and checks, Stop or Autonomy boundary, ownership, and applicable coupling fields sufficient to execute without guessing

#### Scenario: Authoring coverage is checked at start
- **WHEN** a relevant critical expectation is not covered by an executable slice, durably deferred, or explicitly discarded with rationale
- **THEN** capsule compilation and `task-start` fail
- **AND THEN** implementation returns to OpenSpec authoring before product writes

#### Scenario: Incomplete selected slice hard-stops
- **WHEN** the selected current slice has an unresolved or ambiguous Covers reference, missing mode-specific scope, unsupported verification strategy, missing check, or incomplete stop/coupling authority
- **THEN** Keel requires the agent to stop before implementation and repair the OpenSpec task contract

#### Scenario: Future slices may stay rough
- **WHEN** a task file contains future or non-current slices
- **THEN** Keel allows those slices to remain non-executable drafts
- **AND THEN** Keel prohibits selecting those rough slices, projecting them into a native goal, or marking them complete

### Requirement: Completion Gate closes expectation evidence

Keel MUST define a Completion Gate that prevents completion claims until each critical expectation related to the completed work is verified, deferred to a durable owner, or explicitly discarded with rationale.

#### Scenario: Completed work has evidence closure
- **WHEN** an agent reports a task slice or task group complete
- **THEN** Keel guidance requires each related critical expectation to have behavior evidence, a durable follow-up owner, or an explicit discard reason
- **AND THEN** Keel guidance requires completion reporting to preserve unresolved follow-ups outside `keel/HANDOFF.md`

#### Scenario: Missing closure blocks completion
- **WHEN** a related critical expectation lacks evidence, durable owner, or discard rationale
- **THEN** Keel guidance prevents the agent from claiming completion until the expectation is closed or the task contract is updated

### Requirement: Keel keeps expectation gates lightweight

Keel MUST limit expectation gates to execution alignment checks and MUST NOT turn them into broad code quality review.

#### Scenario: Gates check alignment only
- **WHEN** Keel guidance describes Task Authoring, Slice Start, or Completion gates
- **THEN** the gate checks expectation coverage, executable task contracts, or evidence closure
- **AND THEN** the gate does not claim to replace tests, code review, `keel-review-checklist`, or implementation quality judgment

### Requirement: Critical statements carry minimal provenance

Keel MUST distinguish critical accepted decisions, verified facts, assumptions, and unresolved questions inside existing OpenSpec sections without requiring a separate knowledge ledger.

#### Scenario: Critical statements use stable kind identifiers
- **WHEN** a statement affects scope, Acceptance, completion, or execution boundaries
- **THEN** it may use `D<n>`, `F<n>`, `A<n>`, or `Q<n>` according to its kind
- **AND THEN** it records a basis
- **AND THEN** assumptions and unresolved questions record a resolution gate or owner

#### Scenario: Tasks reference relevant provenance
- **WHEN** a critical decision, fact, assumption, or question affects an executable task
- **THEN** the task Covers field references its identifier
- **AND THEN** an implementation task does not proceed through an unresolved question that lacks authorized fallback

#### Scenario: Ordinary narrative remains lightweight
- **WHEN** background text does not affect completion or execution boundaries
- **THEN** Keel does not require a provenance identifier for that text

### Requirement: Completion evidence includes semantic Review

Keel task Evidence MUST record the current agent's minimal semantic completion Review without creating a separate review artifact.

#### Scenario: Review records required judgments
- **WHEN** a task is ready for completion
- **THEN** its Evidence records Review `Status`, `Acceptance check`, `Scope check`, and `Findings`
- **AND THEN** the Review remains in the task's durable owner

#### Scenario: Report is not hidden gate state
- **WHEN** an agent produces the user-facing task Report
- **THEN** the Report summarizes delivery
- **AND THEN** required gate state remains in task Evidence rather than only in chat output

### Requirement: HANDOFF remains pointer-only

Keel MUST treat `keel/HANDOFF.md` as an optional override pointer and MUST NOT use it as the durable owner for expectation state, slice progress, evidence details, or a conversation summary.

#### Scenario: Cross-session continuation normally uses computed context
- **WHEN** Keel can uniquely derive the current owner and next action from explicit input or OpenSpec
- **THEN** continuation does not require `keel/HANDOFF.md`
- **AND THEN** detailed expectation state, slice progress, and evidence remain in OpenSpec artifacts

#### Scenario: Ambiguous continuation may use an override pointer
- **WHEN** human intent cannot be inferred uniquely
- **THEN** a versioned HANDOFF may point to the relevant OpenSpec owner and action with a concise reason
- **AND THEN** the full recovery context remains in design, specs, tasks, or archive evidence

### Requirement: Keel version reflects expectation gate capability

Keel MUST release the stateless continuity, deterministic Core gate, semantic Review, provenance, and capability-adapter contract as version `3.0.0` and keep versioned package, plugin, protocol, build/install/validation, overlay, and generated assets aligned.

#### Scenario: Package and plugin report the new capability version
- **WHEN** the Keel package metadata, plugin metadata, or CLI version is inspected after implementation
- **THEN** the reported Keel version is `3.0.0`
- **AND THEN** dependency versions are not changed by this version bump

#### Scenario: Versioned protocol and generated assets agree
- **WHEN** Keel source assets, installed target protocol assets, build/install/validation constants, OpenSpec overlay markers, or generated `dist/` assets are inspected after implementation
- **THEN** their Keel protocol/version markers use `3.0.0`
- **AND THEN** no current generated target asset continues to advertise `2.7.0`

### Requirement: Compact tasks do not duplicate accepted expectations
Keel MUST keep accepted observable behavior in OpenSpec specs or identified critical statements and MUST allow a task to reference that authority rather than restating it. A task-specific Acceptance clause is permitted only for a slice boundary or observable outcome not already expressed by the referenced authority.

#### Scenario: Covers is sufficient
- **WHEN** referenced scenarios fully define the slice's observable outcomes
- **THEN** the compact task omits duplicated Acceptance prose
- **AND THEN** the capsule records the resolved outcomes and provenance

#### Scenario: Task-specific delta is needed
- **WHEN** the slice narrows an authorized scenario or requires an additional observable completion boundary
- **THEN** the task records only that Acceptance delta
- **AND THEN** the capsule combines it with, but does not replace, the referenced authority

### Requirement: Verification strategy is selected during task authoring
Before a task becomes executable, Keel authoring guidance MUST select the least-cost verification strategy that still proves its resolved Acceptance and MUST record any justified downgrade from test-first behavior.

#### Scenario: New deterministic behavior uses vertical TDD
- **WHEN** a task adds independently testable deterministic behavior
- **THEN** its default strategy is vertical-tdd with one behavior check taken red then green at a time

#### Scenario: Bug uses regression-first
- **WHEN** a task repairs an observable defect
- **THEN** its strategy first reproduces the defect through the public interface and then proves the fix

#### Scenario: Alternative evidence is justified
- **WHEN** strict red-green would not add meaningful proof for a docs, diagnosis, configuration, generated snapshot, or expensive interactive surface
- **THEN** authoring chooses the applicable characterization, rendered-behavior, snapshot-characterization, or evidence-first strategy
- **AND THEN** the task states the observable proof rather than silently downgrading to build success

### Requirement: Task Authoring Gate consumes aligned expectations
Before an affected task can become executable, Keel MUST require every material expectation discovered by quick/deep alignment to be accepted into durable authority, verified as a fact, assigned to a durable owner, or explicitly discarded with rationale.

#### Scenario: Aligned scenario becomes a slice
- **WHEN** alignment accepts an observable positive, negative, edge, or failure behavior
- **THEN** a spec scenario owns it and an applicable task Covers that authority
- **AND THEN** verification names evidence capable of proving it

#### Scenario: Non-goal is protected
- **WHEN** alignment accepts a non-goal or forbidden side effect that constrains execution
- **THEN** design/spec/task authority records it as a scope or stop boundary
- **AND THEN** task-start does not permit a slice whose capsule contradicts it

#### Scenario: Deferred expectation has an owner
- **WHEN** a material expectation is intentionally out of scope for the current change
- **THEN** it names a durable OpenSpec/archive owner and rationale
- **AND THEN** HANDOFF or chat memory is not accepted as that owner

### Requirement: Alignment is semantic and gates remain structural
Keel's deterministic gates MUST validate the durable shape and references created by alignment but MUST NOT claim to infer unstated user intent or replace current-agent semantic review.

#### Scenario: Structural alignment shape is missing
- **WHEN** an affected task references an unresolved Q, missing scenario, unowned material expectation, or absent observable verification boundary
- **THEN** deterministic authoring/start gates block the task

#### Scenario: User intent sufficiency is judged
- **WHEN** all required alignment references are structurally present
- **THEN** the current agent still judges whether they faithfully reflect user intent and repository facts
- **AND THEN** that judgment is recorded in authoring/task Review rather than hidden Core state
