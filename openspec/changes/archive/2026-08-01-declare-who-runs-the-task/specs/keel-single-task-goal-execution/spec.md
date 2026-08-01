## MODIFIED Requirements

### Requirement: Current agent owns implementation and completion
The current agent MUST remain the sole holder of write authority and MUST own fallback, command evidence, semantic Review, gate invocation, task checkbox, and completion reporting decisions throughout the goal run. Where delegation is declared, an authorized delegate MAY perform writes, and only inside the `Touch` boundary that authority already defined; the delegate acquires none of the owned decisions, and the current agent MUST re-run each `M<n>` check itself before recording Evidence.

#### Scenario: Native evaluator reports success
- **WHEN** a native goal evaluator reports that its condition is met
- **THEN** the current agent recomputes the selected task and verifies durable completion
- **AND THEN** evaluator success alone does not mark or report the OpenSpec task complete

#### Scenario: Durable completion is reached
- **WHEN** Acceptance behavior is evidenced, Review passes, `task-complete` passes, and the current agent checks the selected task
- **THEN** the current agent surfaces the final evidence to the native goal
- **AND THEN** the goal ends without transferring completion authority

#### Scenario: Goal stops prematurely
- **WHEN** a native evaluator clears or achieves the goal before durable completion
- **THEN** Keel treats the event as a premature stop
- **AND THEN** it does not automatically rearm a replacement goal

#### Scenario: A declared delegate implements within the goal run
- **WHEN** delegation is declared for the selected task and a guard manifest is active
- **THEN** the delegate may write inside `Touch` while the current agent keeps fallback, Review, gate invocation, the checkbox, and completion reporting
- **AND THEN** the current agent re-runs each `M<n>` check and records its own results as Evidence

#### Scenario: Delegation fields must fit the activation budget
- **WHEN** adding the delegation fields would push the compiled goal condition past the 4,000-character budget
- **THEN** Keel refuses activation rather than omitting Acceptance, fingerprint, stop authority, or the write boundary
- **AND THEN** the refusal names the budget as the reason
