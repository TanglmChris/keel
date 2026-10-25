## MODIFIED Requirements

### Requirement: Deep alignment is the only question-loop entry
Keel MUST use `align-expectations` during OpenSpec authoring so explicit and implicit expectations are aligned before specs and tasks finalize. Deep alignment MUST be the only question-loop entry point: Keel MUST NOT install or document a separate `keel-grill-open-questions` skill or maintain any second authoritative question loop.

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
- **AND THEN** installed documentation and schema guidance reference only `align-expectations` deep alignment

#### Scenario: Missing authority returns to authoring
- **WHEN** implementation discovers an accepted behavior, boundary, or assumption that is not authorized by OpenSpec artifacts
- **THEN** Keel requires the current agent to stop implementation and rerun alignment in authoring
- **AND THEN** stale task authority is reauthored before execution resumes
