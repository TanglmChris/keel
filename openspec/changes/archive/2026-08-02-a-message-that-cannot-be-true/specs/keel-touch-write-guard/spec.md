## ADDED Requirements

### Requirement: A manifest whose change is gone is refused as stale

The write guard MUST distinguish a manifest pointing at a change directory that no longer exists from one whose task it merely cannot match inside a live `tasks.md`. The second is a parse miss the guard MUST continue to refuse to guess about; the first is a fact, and the guard MUST state it.

Keel MUST keep denying the write. Failing closed is what stops archiving a change from silently disabling the guard, so the outcome does not change — only what the refusal says. The message MUST name the action that resolves the state it is refusing, and MUST NOT direct the reader to reauthorize a task that no longer exists.

#### Scenario: An archived change's manifest denies by naming the clear
- **WHEN** a manifest is active and its change directory has been archived
- **THEN** the guard denies the write and reports the manifest as stale, naming `keel guard clear`
- **AND THEN** it does not tell the reader to reauthorize the vanished task through `keel gate task-start`

#### Scenario: A task missing from a live tasks.md is unchanged
- **WHEN** a manifest's change directory exists but its task id is absent from `tasks.md`
- **THEN** the guard behaves exactly as it did before this requirement, enforcing Touch
- **AND THEN** the stale-manifest message is not produced
