# keel-portable-task-execution Specification

## Purpose
Expose the identity and recorded chat closure of a Keel task by its original todo ID, independently of the native execution session.

## Requirements

### Requirement: Query a chat-backed task by its stable identity

For an existing todo, `keel chat show <id> --json` SHALL return a `task` member with `id` equal to the original todo ID and a chat `state` of `open` or `closed`. A closed task SHALL project `closureRecordId` from the first existing `done` record that targets the todo in the group's log order. For an open task, `closureRecordId` SHALL be null. The query SHALL preserve the existing record and reader information, and SHALL leave chat state and cursors untouched. A chat closure is an auditable declaration and does not verify an execution outcome.

#### Scenario: A task is queried before and after a completion reply
- **WHEN** a caller queries an open todo by ID and later queries that same ID after a reply creates a closure record
- **THEN** the query returns the same task ID, with open state and a null receipt before the reply, and closed state with the original closure record ID after it
- **AND THEN** repeated queries and group archival preserve the task identity and receipt

#### Scenario: Other records retain their existing response
- **WHEN** a caller queries a message or a closure record directly
- **THEN** the response retains its existing JSON representation without a task member

### Requirement: Inspect a durable managed Codex delivery receipt

Keel MUST bind new managed delivery claims to the recorded thread before submitting a turn and retain that thread with an acknowledgement. The managed role receipt query MUST use durable local claims. The query MUST NOT infer thread identity from the current role for an older claim or treat an uncertain submission as a native acknowledgement.

#### Scenario: The source role has handed over
- **WHEN** a receipt is queried by its record ID after a managed role changes thread
- **THEN** the query reports the recorded acknowledgement with the original thread and turn without contacting either native thread

#### Scenario: A claim is pending or predates the stored thread ID
- **WHEN** a claim has no acknowledgement or lacks its original thread reference
- **THEN** the query preserves known fields and explicitly reports unknown submission or missing provenance without creating or retrying a turn

### Requirement: Project delivery evidence in the portable task query

For a todo, `keel chat show <id> --json` SHALL include a sibling `delivery` object with a `state` of `unobserved`, `acknowledged` or `unknown`. The query SHALL use local durable evidence for the assignee and the original todo ID. It SHALL preserve chat closure and consult no native runtime. Delivery evidence SHALL NOT certify successful execution or authorize dispatch.

#### Scenario: An upper client reads the same task before and after delivery
- **WHEN** a todo has no observed submission and later acquires a durable acknowledgement
- **THEN** that same query reports unobserved and then acknowledged while keeping the original todo ID and chat state

#### Scenario: A native outcome is ambiguous or not observable
- **WHEN** a matching claim lacks an acknowledgement or the local receipt cannot be interpreted
- **THEN** the query reports unknown and retains the chat task
- **WHEN** no runtime evidence was captured for an assignee
- **THEN** the query reports unobserved without starting or retrying any work
