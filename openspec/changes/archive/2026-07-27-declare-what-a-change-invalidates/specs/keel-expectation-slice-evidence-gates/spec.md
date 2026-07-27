## ADDED Requirements

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
