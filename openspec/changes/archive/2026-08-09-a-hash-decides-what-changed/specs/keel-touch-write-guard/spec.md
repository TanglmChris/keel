## MODIFIED Requirements

### Requirement: The manifest records what was dirty when the task started

The guard manifest MUST record the repository's dirty-path set at the moment `keel gate task-start` authorizes a task, alongside the fingerprint and Touch it already records. That record is what lets the completion gate attribute a later write to the task without a caller-supplied comparison base, and the moment it is taken is what makes it meaningful: any other moment answers a different question.

The recorded set MUST be produced by the same worktree reading the completion gate uses, so the two cannot disagree about which paths are dirty or how a rename is represented. It MUST be taken before the manifest itself is written, so the manifest never appears as a path the task authored.

Each recorded path MUST carry a content signature taken at that same moment — a hash of the path's content, or an explicit absent marker for a path with nothing to read. The signature is what lets the completion gate tell a path still holding the content it held at task start from one the task went on to change again; a bare path name cannot make that distinction, and MUST NOT be recorded alone.

The manifest remains disposable local state. A manifest carrying no such record MUST NOT be treated as recording an empty one, and the completion gate MUST fall back to unattributed reporting instead, because a missing record and a clean start are different facts and only one of them can be proved.

#### Scenario: The set is recorded when the task is authorized
- **WHEN** `keel gate task-start` writes the guard manifest for a task
- **THEN** the manifest records the dirty-path set observed at that moment
- **AND THEN** the manifest's own path is not part of that set

#### Scenario: The recorded set carries a content signature
- **WHEN** `keel gate task-start` records a dirty path
- **THEN** the manifest carries that path's content signature alongside its name
- **AND THEN** a path with nothing to read at that moment records an explicit absent signature rather than omitting the entry or recording the path name alone

#### Scenario: A manifest without the record does not claim a clean start
- **WHEN** the completion gate reads a manifest carrying no recorded dirty-path set
- **THEN** it reports dirty paths without attributing them
- **AND THEN** it does not fail the task on paths it cannot attribute
