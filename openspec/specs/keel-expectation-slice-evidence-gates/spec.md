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
- **WHEN** authoring grill or a domain lens identifies accepted hidden-knowledge assumptions
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

### Requirement: Gate-validated forms are expressed in the author-facing surface

Every form that a completion or close gate hard-validates MUST be expressed in
the author-facing surface an author reads — the `keel-spec-driven` tasks template
and the `tasks` artifact authoring instruction — not only in the validators. An
author who follows the shipped template and instruction MUST NOT hit an avoidable
completion or close hard-stop over a form the surface never described.

#### Scenario: Accepted Review Status tokens are documented for authors

- **WHEN** an author consults the `keel-spec-driven` tasks template or its `tasks` artifact instruction
- **THEN** the accepted Review `Status` tokens are enumerated there, including `done`
- **AND THEN** the author can record a passing Status without reading gate source

#### Scenario: Accepted Findings forms are documented for authors

- **WHEN** an author consults the tasks template or the `tasks` artifact instruction
- **THEN** the accepted Findings forms are enumerated: `none`, or a recorded finding carrying a durable owner — a `discard reason:`/`discard rationale:` prefix, a `keel/archive/…` path, an existing `openspec/changes/…` artifact, or any other repo-relative path that exists
- **AND THEN** the surface states that an observation worth recording must take one of these owned forms rather than a bare note, so it does not fail `finding-owner`

#### Scenario: Expectation Coverage section ships in the template

- **WHEN** an author starts a change from the `keel-spec-driven` tasks template
- **THEN** the template already contains a `## Expectation Coverage` section carrying a `- None.` default and an `- E<n>: … Covered by: <task ids>` example
- **AND THEN** the `tasks` artifact instruction requires and formats that section so `change-close` finds it rather than the author discovering the requirement only at close
### Requirement: Task Authoring Gate covers statements the change invalidates

A change that alters a behavior leaves standing every statement that described
the old one. Before any task of a change is executable, tasks.md MUST declare
the statements this change invalidates, in a section the Task Authoring Gate
checks. Each declaration MUST carry a searchable symptom phrase — the wording a
reader looking for the stale statement would actually search for — because the
text that rots is the text the author was not already holding in mind, and a
location list only ever names files the author already recalled. Each
declaration MUST also close: updated by named tasks of this change, deferred to
a durable owner, or discarded with a stated reason. A change that invalidates
nothing MUST be able to say so in one line.

The check is structural, not semantic. Keel MUST NOT attempt to judge whether
the declared phrase is the right one or whether the located text was correctly
updated; that judgment belongs to the current agent's review.

#### Scenario: A change with no declaration cannot start its tasks
- **WHEN** `keel gate task-start` runs for a change whose tasks.md has no invalidation section
- **THEN** the gate fails with a problem naming the missing section and the closure forms it accepts
- **AND THEN** no guard manifest and no contract anchor are written

#### Scenario: Declaring nothing is a legitimate answer
- **WHEN** a change's invalidation section states that nothing is invalidated
- **THEN** the Task Authoring Gate accepts it and the change's tasks become executable
- **AND THEN** no further entry is demanded of that change

#### Scenario: A location without a symptom phrase is refused
- **WHEN** an invalidation entry names only files or paths and carries no searchable symptom phrase
- **THEN** the gate fails with a problem stating that the entry needs the wording a reader would search for
- **AND THEN** the diagnostic identifies which entry is incomplete

#### Scenario: An entry must close
- **WHEN** an invalidation entry carries neither tasks that update it, nor a durable owner, nor a discard reason
- **THEN** the gate fails with a problem naming that entry as unclosed
- **AND THEN** the accepted closure forms are stated in the diagnostic

#### Scenario: Declared updates land in Touch before implementation
- **WHEN** an invalidation entry names tasks of this change as its updater
- **THEN** the declaration exists while tasks are being authored, so the affected paths can be declared in those tasks' Touch from the start
- **AND THEN** discovering the documentation surface does not require reauthorizing a capsule mid-task

#### Scenario: The declaration is not task authority
- **WHEN** the invalidation section changes
- **THEN** no task capsule fingerprint changes, because the section lives outside every task body
- **AND THEN** the section is not read as Acceptance, Touch, or verification authority

### Requirement: A durable owner may be any file the repository keeps, and a refusal names what it accepts

The accepted durable-owner forms are shape checks. A gate runs without network
and cannot confirm that a URL resolves or that an archive path is the right one,
so a whitelist of prefixes verifies nothing beyond spelling. A repo-relative path
is the one form a gate can actually check, and refusing it while accepting the
unverifiable ones inverts the rigour.

A `Durable owner:` MUST therefore be accepted when it names a repo-relative path
that exists in the repository the gate is running against, in addition to the
forms already accepted. A path that does not exist MUST be refused, which is a
check the prefix whitelist could not make. `keel/HANDOFF.md` MUST stay refused
even though it exists, because the protocol defines it as a pointer override
rather than an owner: existence is necessary, not sufficient.

The same vocabulary MUST apply wherever a durable owner closes an entry —
Review `Findings`, `## Expectation Coverage`, and `## Invalidates` — so a form
accepted in one place is never refused in another. Every refusal of an owner or
a closure MUST state the forms it would accept, because an author who cannot
see the boundary can only find it by trial.

#### Scenario: A repo ledger is a legitimate owner

- **WHEN** an entry closes with a `Durable owner:` naming a repo-relative file that exists
- **THEN** the gate accepts it
- **AND THEN** the same path is accepted whether it closes an invalidation, an expectation, or a review finding

#### Scenario: An owner that does not exist is refused

- **WHEN** a `Durable owner:` names a repo-relative path with no file behind it
- **THEN** the gate refuses the entry and says the path does not exist
- **AND THEN** the refusal is distinguishable from an entry that named no owner at all

#### Scenario: The pointer override is still not an owner

- **WHEN** a `Durable owner:` names `keel/HANDOFF.md`
- **THEN** the gate refuses it even though the file exists
- **AND THEN** the refusal states that this file is a pointer override rather than a durable owner

#### Scenario: A refusal states the accepted forms

- **WHEN** a gate refuses an entry for lacking a closure or a valid owner
- **THEN** the diagnostic names the forms it accepts, including the existing-path form
- **AND THEN** the author does not have to discover the boundary by trying candidates

### Requirement: Shipped version markers agree with the package version

A requirement that names the version being released is true for one release and
false for every release after it, while reading as a standing rule. What the
rule was reaching for is the invariant, not the number: **every version marker
Keel ships MUST agree with the package version**, across npm metadata, both
native plugin manifests, protocol and bootstrap markers, build/install/validation
constants, and the OpenSpec overlay markers of every initialized target.

The invariant MUST be enforced by a check rather than asserted, and that check
MUST derive the markers it compares from what the repository actually ships
rather than from a fixed list, because a fixed list is the next thing to fall
behind. The release bump MUST refresh every initialized target's markers, not
only those of the target it happens to touch: a marker that only a human
remembers to update falls behind by one version per release, silently, because
nothing fails when it does.

#### Scenario: Every shipped marker matches the package version

- **WHEN** the repository's shipped version markers are inspected at any commit
- **THEN** each one reports the package version
- **AND THEN** a marker left behind fails the check and is named with its path

#### Scenario: The release bump reaches every target

- **WHEN** the version is bumped for a release
- **THEN** the overlay markers of every initialized target are refreshed together
- **AND THEN** no target's markers depend on a separate manual step

#### Scenario: The marker list is derived, not fixed

- **WHEN** a new shipped surface carrying a version marker is added
- **THEN** the check covers it without being edited
- **AND THEN** the invariant cannot be satisfied by a list that stopped tracking reality
