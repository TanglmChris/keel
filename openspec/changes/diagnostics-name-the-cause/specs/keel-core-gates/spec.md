## ADDED Requirements

### Requirement: task-complete infers only a task that has started
When no task is named explicitly, `task-complete` MUST NOT infer a task whose Evidence `Contract` anchor holds no compiled fingerprint. It MUST refuse with a selection diagnostic that names the task it would have inferred, the most recently checked task, and the explicit selection flag. `task-start` MUST keep the first-unchecked default, because a task that has not started is the task it selects.

#### Scenario: The inferred task has never started
- **WHEN** `task-complete` runs without an explicit task and the first unchecked task records no fingerprint in its Evidence `Contract` anchor
- **THEN** the gate refuses on selection rather than reporting that task's readiness problems
- **AND THEN** the diagnostic names the inferred task, the most recently checked task, and the explicit selection flag

#### Scenario: The inferred task has recorded its start fingerprint
- **WHEN** `task-complete` runs without an explicit task and the first unchecked task records a compiled fingerprint in its Evidence `Contract` anchor
- **THEN** the gate evaluates that task's completion evidence as before

#### Scenario: An explicitly named task is never second-guessed
- **WHEN** `task-complete` runs with an explicit task selection
- **THEN** the selection diagnostic does not apply and the named task is evaluated
