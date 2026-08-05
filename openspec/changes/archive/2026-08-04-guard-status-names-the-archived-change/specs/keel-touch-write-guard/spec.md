## MODIFIED Requirements

### Requirement: A manifest whose change is gone is refused as stale

Keel MUST distinguish a manifest pointing at a change directory that no longer exists from one whose task it merely cannot match inside a live `tasks.md`. The second is a parse miss Keel MUST continue to refuse to guess about; the first is a fact, and Keel MUST state it.

This distinction MUST hold on every surface that reports the manifest's state — the write guard hook that refuses a write, and `keel guard status` that describes the manifest — and both MUST decide it by testing the same object, the change directory, so that one surface cannot come to disagree with the other about a state a reader is looking at from both. A surface reporting the vanished change MUST carry a distinct problem code, so the two states are separable without matching on message text.

Keel MUST keep denying the write. Failing closed is what stops archiving a change from silently disabling the guard, so the outcome does not change — only what the refusal says. The message MUST name the action that resolves the state it is refusing, and MUST NOT direct the reader to reauthorize a task that no longer exists.

A change directory that exists while its `tasks.md` does not MUST keep the parse-miss treatment. That is a live change mid-authoring, and reauthorizing it is genuinely its way out.

#### Scenario: An archived change's manifest denies by naming the clear
- **WHEN** a manifest is active and its change directory has been archived
- **THEN** the guard denies the write and reports the manifest as stale, naming `keel guard clear`
- **AND THEN** it does not tell the reader to reauthorize the vanished task through `keel gate task-start`

#### Scenario: A task missing from a live tasks.md is unchanged
- **WHEN** a manifest's change directory exists but its task id is absent from `tasks.md`
- **THEN** the guard behaves exactly as it did before this requirement, enforcing Touch
- **AND THEN** the stale-manifest message is not produced

#### Scenario: Guard status names the clear for an archived change
- **WHEN** `keel guard status` runs against a manifest whose change directory no longer exists
- **THEN** it reports the manifest as stale, names the directory that is gone, and names `keel guard clear`
- **AND THEN** it does not direct the reader to reauthorize the vanished task, which `keel gate task-start` and `keel guard start` both refuse for a change that is not there

#### Scenario: Guard status is unchanged for a task missing from a live tasks.md
- **WHEN** `keel guard status` runs against a manifest whose change directory exists but whose task id is absent from `tasks.md`
- **THEN** it reports the same status, the same problem code, and the same message it reported before this requirement covered it
- **AND THEN** the two states no longer produce identical output
