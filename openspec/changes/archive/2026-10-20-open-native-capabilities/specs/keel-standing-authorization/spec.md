## RENAMED Requirements

- FROM: `### Requirement: A continuation authorization covers one approved between-task boundary`
- TO: `### Requirement: Continuing to the next approved task needs no authorization`

## MODIFIED Requirements

### Requirement: Continuing to the next approved task needs no authorization

Moving from a durably complete task to the next unchecked task of the same change, inside a change
whose `tasks.md` the owner approved, MUST need no confirmation and no declaration. Each next task
MUST still start through `keel gate task-start` with its own recorded fingerprint, and every gate,
evidence requirement, semantic Review, and write-guard step MUST run unchanged. A stop with its own
trigger — a blocker, fingerprint drift, an out-of-scope need, a material choice escalated by
alignment, an unresolved `Q<n>`, a task's own Stop Rules — MUST halt. Continuing MUST NOT select work
outside the change or outside the approved `tasks.md` order, and MUST NOT authorize any repository
action — `commit`, `push`, `release`, and `archive` each still require their own name.

A declared `continuation` MUST remain accepted, because repositories declare it today, and MUST change
no behavior.

#### Scenario: Continuation authorizes no repository action
- **WHEN** `keel/config.yaml` declares `authorize:` listing only `continuation`
- **THEN** Keel resolves `continuation` as standing-authorized and reports it so
- **AND THEN** `commit`, `push`, `release`, and `archive` all remain unauthorized

#### Scenario: A capsule inherits continuation and names its source
- **WHEN** a task authors no `Autonomy boundary:` and the repository authorizes `continuation`
- **THEN** the compiled capsule carries the inherited authorization naming `keel/config.yaml` as
  its source
- **AND THEN** actions the repository did not declare still resolve to hard-stop

#### Scenario: The declaration is inert to gates and selection
- **WHEN** two otherwise identical repositories differ only in a declared `continuation`
- **THEN** every gate returns the same status and problem set in both
- **AND THEN** `keel context` reports the same status and next action in both

#### Scenario: The next task still starts through its own gate
- **WHEN** a task is durably complete and the next unchecked task belongs to the same approved change
- **THEN** the next task starts through `keel gate task-start` without a confirmation
- **AND THEN** its own fingerprint is recorded before implementation, exactly as an attended start
  records one
