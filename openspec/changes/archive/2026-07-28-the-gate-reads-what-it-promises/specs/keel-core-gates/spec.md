## ADDED Requirements

### Requirement: Completion requires a recorded start fingerprint
`task-complete` MUST refuse a task whose Evidence `Contract` anchor holds no compiled fingerprint, whether that task was named explicitly or inferred, and MUST name the command that records one. A task that recorded no anchor has no drift detection, so completion MUST NOT report it as gated. `task-start` MUST NOT require an anchor, because it runs before one can exist.

#### Scenario: A named task with no recorded anchor is refused
- **WHEN** `task-complete` evaluates an explicitly named task whose `Contract` anchor holds no compiled fingerprint
- **THEN** the gate does not pass
- **AND THEN** the diagnostic names the anchor and the command that records it

#### Scenario: A recorded anchor completes as before
- **WHEN** `task-complete` evaluates a task whose `Contract` anchor holds a compiled fingerprint
- **THEN** the anchor is compared against the recompiled fingerprint as before

#### Scenario: task-start does not require an anchor
- **WHEN** `task-start` evaluates a task whose `Contract` anchor holds no compiled fingerprint
- **THEN** the missing anchor is not reported as a problem
