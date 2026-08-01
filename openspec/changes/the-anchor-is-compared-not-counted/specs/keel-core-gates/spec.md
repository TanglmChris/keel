## ADDED Requirements

### Requirement: A recorded anchor is compared against the recompiled fingerprint

`task-complete` MUST recompile the selected task's capsule and compare the result with the fingerprint recorded in its Evidence `Contract` anchor. A difference MUST fail the gate. It MUST NOT be reported as a warning or as `needs-review`, because drift returns the task to authoring rather than to the judgment of the agent recording its own Review.

The diagnostic MUST name the recorded value, the recompiled value, and the command that reauthorizes the task, and MUST state that execution evidence produced under the previous contract is stale.

Keel MUST NOT require the anchor to carry a capsule schema prefix. A fingerprint is a digest over the canonical capsule serialization, so a value that matches could only have come from the schema that produced it; the prefix is diagnostic detail, not a gate condition.

#### Scenario: A contract edited after recording is refused
- **WHEN** a task's Touch, Verify, Covers, or a boundary is changed after its anchor was recorded, and `task-complete` evaluates it
- **THEN** the gate fails with a contract-drift diagnostic
- **AND THEN** the diagnostic names both the recorded and the recompiled fingerprint, names the reauthorization command, and states that evidence recorded under the previous contract is stale

#### Scenario: An anchor holding a foreign fingerprint is refused
- **WHEN** the recorded anchor is a well-formed digest that the task's own capsule does not compile to
- **THEN** the gate fails rather than accepting the anchor on its shape
- **AND THEN** a value of sixty-four zeros is refused for the same reason as any other non-matching value

#### Scenario: A matching anchor completes
- **WHEN** the recorded anchor equals the recompiled fingerprint
- **THEN** the comparison contributes no problem and the task's other completion evidence is evaluated as usual

#### Scenario: A schema prefix is not required
- **WHEN** the anchor records a bare `sha256:` digest with no capsule schema prefix, and that digest matches
- **THEN** the gate does not refuse it for the missing prefix

### Requirement: change-close compares the anchor of every checked task

`change-close` MUST compare each checked task's recorded anchor against its recompiled fingerprint, and MUST fail on a difference. A checked task that records no anchor MUST also fail, because an absent record and a drifted one are the same absence of proof at the gate that closes a live change.

The close diagnostic MUST identify the task and MUST NOT direct the reader to complete a task that is already checked.

#### Scenario: Drift introduced after completion is caught at the close
- **WHEN** every task is checked, a task's contract is then edited without reauthorizing, and `change-close` runs
- **THEN** the gate fails and names the task whose anchor no longer matches

#### Scenario: A checked task with no anchor fails the close
- **WHEN** a checked task's Evidence `Contract` anchor holds no compiled fingerprint and `change-close` runs
- **THEN** the gate fails rather than closing a change whose completion cannot be verified
- **AND THEN** the diagnostic does not tell the reader to complete a task that is already complete

#### Scenario: An unchanged change closes as before
- **WHEN** every checked task's anchor matches its recompiled fingerprint
- **THEN** the anchor comparison contributes no problem

## MODIFIED Requirements

### Requirement: Completion requires a recorded start fingerprint
`task-complete` MUST refuse a task whose Evidence `Contract` anchor holds no compiled fingerprint, whether that task was named explicitly or inferred, and MUST name the command that records one. A task that recorded no anchor has no drift detection, so completion MUST NOT report it as gated. `task-start` MUST NOT require an anchor, because it runs before one can exist.

#### Scenario: A named task with no recorded anchor is refused
- **WHEN** `task-complete` evaluates an explicitly named task whose `Contract` anchor holds no compiled fingerprint
- **THEN** the gate does not pass
- **AND THEN** the diagnostic names the anchor and the command that records it

#### Scenario: A recorded anchor is compared, not counted
- **WHEN** `task-complete` evaluates a task whose `Contract` anchor holds a compiled fingerprint
- **THEN** the anchor is compared against the recompiled fingerprint, and a difference fails the gate
- **AND THEN** the presence of a well-formed digest is not by itself sufficient to satisfy the anchor requirement

#### Scenario: task-start does not require an anchor
- **WHEN** `task-start` evaluates a task whose `Contract` anchor holds no compiled fingerprint
- **THEN** the missing anchor is not reported as a problem
