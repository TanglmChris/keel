## Purpose

Define how Keel surfaces hidden-knowledge risk during OpenSpec authoring and keeps accepted decisions durable.
## Requirements
### Requirement: Hidden knowledge is captured durably
Keel MUST require accepted explicit requirements, implicit expectations, answers, assumptions, non-goals, observable acceptance, evidence boundaries, and constraints discovered during alignment to be captured in durable OpenSpec or Keel artifacts rather than chat memory.

#### Scenario: Alignment outcomes are written back
- **WHEN** quick or deep alignment establishes authoring authority
- **THEN** Keel routes the outcome to proposal, design, specs, or tasks according to its ownership
- **AND THEN** future agents do not need chat history to recover it

#### Scenario: Unaccepted inference stays unresolved
- **WHEN** an inferred material expectation has not been accepted or verified
- **THEN** it remains a Q<n> or is explicitly discarded with rationale
- **AND THEN** it does not appear as accepted spec behavior

#### Scenario: Handoff remains pointer-only
- **WHEN** a session needs future continuation context after expectation discovery
- **THEN** Keel keeps detailed recovery context in design, specs, tasks, archive evidence, or explicit discard rationale
- **AND THEN** `keel/HANDOFF.md` only points to those durable owners

### Requirement: Native planning artifacts funnel into OpenSpec authority
An accepted native plan-mode artifact MUST NOT serve as execution authority; its scope-, acceptance-, or boundary-affecting decisions MUST land in OpenSpec artifacts before implementation begins.

#### Scenario: Accepted plan is solidified before implementation
- **WHEN** a native plan is accepted and work proceeds toward implementation
- **THEN** the plan's decisions affecting scope, Acceptance, completion, or execution boundaries are recorded in proposal, design, specs, or tasks
- **AND THEN** the session plan file is not cited as execution authority

#### Scenario: Review checks the funnel
- **WHEN** the review checklist runs for work that followed an accepted native plan
- **THEN** it verifies the plan's material decisions exist in OpenSpec artifacts
- **AND THEN** decisions found only in session state are treated as missing authority returning to OpenSpec authoring

### Requirement: Deep alignment is the only question-loop entry
Keel MUST use `keel-align-expectations` during OpenSpec authoring so explicit and implicit expectations are aligned before specs and tasks finalize. Deep alignment MUST be the only question-loop entry point: Keel MUST NOT install or document a separate `keel-grill-open-questions` skill or maintain any second authoritative question loop.

#### Scenario: Quick alignment is sufficient
- **WHEN** proposal context and repository evidence establish complete low-risk authority
- **THEN** Keel runs a compact alignment summary and proceeds without a blocking question loop
- **AND THEN** accepted goals, non-goals, Acceptance, and evidence remain durable

#### Scenario: Risk-triggered deep alignment is required
- **WHEN** proposal, design, specs, or tasks touch a high-risk domain, external interface, security or permission boundary, state or protocol boundary, UI-observable behavior, generated artifact, or material task contract field that cannot be written without guessing
- **THEN** Keel guidance requires the deep alignment question loop before specs/tasks finalize or the affected task becomes executable
- **AND THEN** the loop stays limited to material uncertainty and asks one decision at a time

#### Scenario: Retired grill surface is removed conservatively
- **WHEN** `keel --install` or `keel --init` runs against a target repo carrying a previously packaged `keel-grill-open-questions` skill copy
- **THEN** a byte-identical packaged copy is removed and a user-modified copy is preserved with a manual migration warning
- **AND THEN** installed documentation and schema guidance reference only `keel-align-expectations` deep alignment

#### Scenario: Missing authority returns to authoring
- **WHEN** implementation discovers an accepted behavior, boundary, or assumption that is not authorized by OpenSpec artifacts
- **THEN** Keel requires the current agent to stop implementation and rerun alignment in authoring
- **AND THEN** stale task authority is reauthored before execution resumes

