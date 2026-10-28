## ADDED Requirements

### Requirement: An archived guard manifest is not a task in progress

`keel shift check` MUST NOT report as an item a `keel/guard.json` that `keel guard status` reads as `archived`, because that manifest enforces nothing; it MUST report it as a note naming `keel guard clear`. A manifest in any other state MUST still be reported as an item.

#### Scenario: A manifest over an archived task does not block the hand-over
- **WHEN** a worktree is otherwise clean and its `keel/guard.json` guards a task that is checked in its change's archived copy
- **THEN** `keel shift check` exits 0, reports no `task-in-progress` item, and prints a note naming `keel guard clear`

#### Scenario: A manifest over a live task still blocks it
- **WHEN** the same worktree's manifest guards a task of a change that is not archived
- **THEN** `keel shift check` exits 1 and reports `task-in-progress`
