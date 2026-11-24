## ADDED Requirements

### Requirement: Query a chat-backed task by its stable identity

For an existing todo, `keel chat show <id> --json` SHALL return a `task` member with `id` equal to the original todo ID and a chat `state` of `open` or `closed`. A closed task SHALL project `closureRecordId` from the first existing `done` record that targets the todo in the group's log order. For an open task, `closureRecordId` SHALL be null. The query SHALL preserve the existing record and reader information, and SHALL leave chat state and cursors untouched. A chat closure is an auditable declaration and does not verify an execution outcome.

#### Scenario: A task is queried before and after a completion reply
- **WHEN** a caller queries an open todo by ID and later queries that same ID after a reply creates a closure record
- **THEN** the query returns the same task ID, with open state and a null receipt before the reply, and closed state with the original closure record ID after it
- **AND THEN** repeated queries and group archival preserve the task identity and receipt

#### Scenario: Other records retain their existing response
- **WHEN** a caller queries a message or a closure record directly
- **THEN** the response retains its existing JSON representation without a task member
