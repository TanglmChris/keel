# keel-single-task-goal-execution Specification

## Purpose
TBD - created by archiving change native-single-task-goal-execution. Update Purpose after archive.
## Requirements
### Requirement: Single-task goal activation is explicit and fingerprinted
Keel MUST activate native goal execution only for one explicitly selected OpenSpec task whose `task-start` gate passes, and MUST bind the authorization to that task's capsule fingerprint.

#### Scenario: User authorizes one task
- **WHEN** the user explicitly requests automatic execution of one selected task
- **AND WHEN** `task-start` returns a passing capsule and fingerprint
- **THEN** the current agent records the single-task authorization and start fingerprint in that task's Evidence
- **AND THEN** Keel projects exactly that task into the target goal surface

#### Scenario: Ambiguous selection does not start
- **WHEN** the requested work does not resolve to exactly one executable task
- **THEN** Keel does not create a goal or perform product writes
- **AND THEN** it reports the candidate owners or missing authority

#### Scenario: Task group is rejected
- **WHEN** activation requests multiple tasks, a contiguous task group, a change backlog, or an implicit next task
- **THEN** Keel rejects the goal projection
- **AND THEN** it asks for one task selection without broadening the authorization

### Requirement: Goal projection is derived from the task capsule
Keel MUST compile a versioned disposable goal projection from the selected task capsule, including the objective, resolved Acceptance, named Commands, verification strategy, Touch boundary, Stop or Autonomy boundary, fingerprint, and evidence needed for completion.

#### Scenario: Complete projection is compiled
- **WHEN** a passing capsule is projected for a supported target
- **THEN** the goal condition names one measurable end state and its proof
- **AND THEN** it retains all execution and stop boundaries needed to prevent scope drift

#### Scenario: Target length cannot preserve authority
- **WHEN** the target goal limit cannot contain a projection that preserves required authority
- **THEN** Keel refuses native activation or reports a manual fallback
- **AND THEN** it does not silently omit Acceptance, fingerprint, or stop conditions

### Requirement: Current agent owns implementation and completion
The current agent MUST remain the sole writer and MUST own fallback, command evidence, semantic Review, gate invocation, task checkbox, and completion reporting decisions throughout the goal run.

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

### Requirement: Execution follows the task verification strategy
The current agent MUST execute the task's approved test-first or evidence-first strategy in vertical behavior slices and MUST NOT let the native loop weaken Commands or Acceptance.

#### Scenario: Behavior supports red green
- **WHEN** the task covers software or pure logic with feasible automated behavior tests
- **THEN** the current agent demonstrates one failing behavior before each minimal implementation slice
- **AND THEN** it demonstrates that behavior passing before the next slice

#### Scenario: Strict red green is not the approved layer strategy
- **WHEN** the task specifies characterization, rendered-interface, hardware-testbench, or another approved evidence-first strategy
- **THEN** the current agent follows that strategy and records its evidence
- **AND THEN** it does not invent a weaker shape-only or build-only substitute

### Requirement: Goal execution stops at the selected task boundary
Keel MUST stop after the selected task is durably complete and MUST require new explicit user authorization before projecting or starting another task.

#### Scenario: Selected task completes
- **WHEN** the selected task becomes durably complete
- **THEN** Keel clears or allows achievement of its native goal and returns control to the user
- **AND THEN** it does not inspect the backlog to start another task

#### Scenario: User later authorizes another task
- **WHEN** the completed run has stopped and the user explicitly names another task for automatic execution
- **THEN** Keel performs a new `task-start` and records a new fingerprinted authorization
- **AND THEN** the previous goal state supplies no authority to the new run

### Requirement: Failure and scope boundaries terminate safely
Keel MUST obey the selected task's Stop and Autonomy boundaries and MUST end or pause the goal loop when continuation lacks pre-authorized authority.

#### Scenario: Pre-authorized fallback applies
- **WHEN** a failure matches an exact reversible fallback in the selected task
- **THEN** the current agent may use that fallback within its stated limit
- **AND THEN** it records the required evidence before continuing

#### Scenario: Hard-stop event occurs
- **WHEN** execution encounters scope expansion, permission need, fingerprint drift, unowned failure, exhausted retry fuse, or another hard-stop condition
- **THEN** the current agent pauses or clears the native goal when possible and records a blocker
- **AND THEN** it returns control without inventing a fallback or rolling back automatically

### Requirement: Helpers are bounded read-only evidence producers
Keel MAY use helpers only when the user or selected task authorizes them, and every helper MUST receive a versioned brief that prohibits repository writes, implementation ownership, nested delegation, acceptance changes, and completion actions.

#### Scenario: Exploration helper is delegated
- **WHEN** an independent read-heavy question can reduce main-agent context
- **THEN** the helper receives only the question, required reads, read-only tools, and report schema
- **AND THEN** its return is evidence for current-agent review

#### Scenario: Verification helper is delegated
- **WHEN** an exact verification command is proven repository-byte-stable or writes only to a declared external temporary location
- **THEN** the helper may run that command and return bounded evidence
- **AND THEN** repository-generating or repair commands remain current-agent work

#### Scenario: Helper changes repository bytes
- **WHEN** before-and-after comparison detects a helper-created repository change
- **THEN** the current agent rejects the helper evidence and stops
- **AND THEN** it reports the changed paths without accepting or automatically cleaning them

#### Scenario: Helper attempts further delegation
- **WHEN** a helper requests, spawns, or transfers work to another helper
- **THEN** the return is rejected as outside its brief
- **AND THEN** no nested helper result becomes task evidence

### Requirement: Manual fallback preserves the same task lifecycle
Keel MUST remain usable when a native goal capability is absent, disabled, untrusted, or behaviorally unverified by executing the same selected capsule through an explicit current-agent manual loop.

#### Scenario: Native goal is unavailable
- **WHEN** capability probing cannot safely activate the target goal surface
- **THEN** Keel reports `advisory` with an exact user command or `manual` with the current-agent loop
- **AND THEN** it does not install a scheduler, global Stop hook, or hidden background process

