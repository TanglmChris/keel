## MODIFIED Requirements

### Requirement: Goal execution stops at the selected task boundary
Keel MUST stop after the selected task is durably complete and MUST require explicit user
authorization before projecting or starting another task. That authorization is either a new
explicit user instruction or a standing `continuation` authorization declared in
`keel/config.yaml`; the standing form covers only the next unchecked task of the same change, in
the approved `tasks.md` order. Either form MUST still pass a new `task-start` with a new recorded
fingerprint, and the previous goal state supplies no authority to the new run.

#### Scenario: Selected task completes
- **WHEN** the selected task becomes durably complete and the repository declares no standing
  `continuation` authorization
- **THEN** Keel clears or allows achievement of its native goal and returns control to the user
- **AND THEN** it does not inspect the backlog to start another task

#### Scenario: User later authorizes another task
- **WHEN** the completed run has stopped and the user explicitly names another task for automatic execution
- **THEN** Keel performs a new `task-start` and records a new fingerprinted authorization
- **AND THEN** the previous goal state supplies no authority to the new run

#### Scenario: A standing continuation authorization is the durable form of the instruction
- **WHEN** a completed run has stopped, the repository declares `continuation` in `authorize:`, and
  the same change's approved `tasks.md` holds a next unchecked task
- **THEN** that next task may start through a new `task-start` with a new recorded fingerprint,
  without a new conversational instruction
- **AND THEN** work outside that change, or outside the approved task order, still requires a new
  explicit user instruction
