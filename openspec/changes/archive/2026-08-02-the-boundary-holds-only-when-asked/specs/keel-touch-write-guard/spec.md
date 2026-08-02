## ADDED Requirements

### Requirement: The manifest records what was dirty when the task started

The guard manifest MUST record the repository's dirty-path set at the moment `keel gate task-start` authorizes a task, alongside the fingerprint and Touch it already records. That record is what lets the completion gate attribute a later write to the task without a caller-supplied comparison base, and the moment it is taken is what makes it meaningful: any other moment answers a different question.

The recorded set MUST be produced by the same worktree reading the completion gate uses, so the two cannot disagree about which paths are dirty or how a rename is represented. It MUST be taken before the manifest itself is written, so the manifest never appears as a path the task authored.

The manifest remains disposable local state. A manifest carrying no such record MUST NOT be treated as recording an empty one, and the completion gate MUST fall back to unattributed reporting instead, because a missing record and a clean start are different facts and only one of them can be proved.

#### Scenario: The set is recorded when the task is authorized
- **WHEN** `keel gate task-start` writes the guard manifest for a task
- **THEN** the manifest records the dirty-path set observed at that moment
- **AND THEN** the manifest's own path is not part of that set

#### Scenario: A manifest without the record does not claim a clean start
- **WHEN** the completion gate reads a manifest carrying no recorded dirty-path set
- **THEN** it reports dirty paths without attributing them
- **AND THEN** it does not fail the task on paths it cannot attribute

### Requirement: The completion gate catches what the guard cannot intercept

Enforcement binds the host's file-writing tools, so a write issued by a shell command reaches the worktree without the guard seeing it. Keel MUST NOT claim otherwise, and MUST NOT rely on the guard alone to keep a task inside its Touch. The completion gate is where such a write is caught, and it MUST catch it in its default invocation rather than only when a caller requests the comparison.

#### Scenario: A shell-issued write outside Touch is caught at completion
- **WHEN** a task writes a file outside its Touch by a means the write guard does not intercept
- **AND WHEN** task completion runs in its default invocation
- **THEN** completion fails naming that path
- **AND THEN** the outcome does not depend on whether the guard observed the write
