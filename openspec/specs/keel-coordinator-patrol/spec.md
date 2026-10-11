## Purpose

Define how a role declares what it is waiting for in the chat, and how a host-scheduled `keel patrol`, run as the coordinator's role, notifies the roles whose conditions are met and routes labelled issue updates to roles, writing nothing when nothing is new and never fetching or scheduling.

## Requirements

### Requirement: A role declares what it is waiting for in the chat

`keel chat wait <group> --commit <sha> [--remote <name>] [note]` and `keel chat wait <group> --issue <n> --closed [note]` MUST write a `wait` record from the caller's role in a group it belongs to, carrying the condition. A wait MUST NOT make anything unread or wake any role. `keel chat waits [--json]` MUST list every wait that no `met` record targets, with its role, group, and condition. Exactly one condition MUST be given, and anything else MUST be refused naming the forms.

#### Scenario: A declared wait is listed until met
- **WHEN** `verify` runs `keel chat wait soc --commit <sha>`
- **THEN** `keel chat waits --json` lists it with role `verify` and condition `commit <sha> on origin`, and nobody has it unread

#### Scenario: A malformed wait is refused
- **WHEN** `keel chat wait soc` names no condition, or both `--commit` and `--issue`
- **THEN** it exits non-zero naming the two forms

### Requirement: Patrol notifies the roles whose conditions are met and writes nothing otherwise

`keel patrol [--issues <file>] [--idle <duration>] [--json]` MUST run as the caller's bound role and MUST NOT fetch, schedule, or call a model. For each open wait in the groups that role can read, it MUST check the condition — a commit contained in a `refs/remotes/<remote>/` ref; an issue that `--issues` lists as closed — and for each that holds MUST write a `met` record targeting the wait and send the waiting role a direct message naming the condition and the wait, unless the waiter is the patrolling role. Without `--issues`, issue conditions MUST be reported unchecked. Patrol MUST list each bound role's presence, last activity, and open todo count, marking a role idle beyond `--idle`. It MUST exit 0 when it wrote nothing, 2 when it wrote at least one record, and 1 on an error; idleness MUST NOT change the exit status.

#### Scenario: A landed commit wakes the waiting role once
- **WHEN** `verify` waits for a commit, the commit reaches `origin`, and `rtl` runs `keel patrol` twice
- **THEN** the first run exits 2, marks the wait met, and `verify` has a direct message from `rtl` naming the commit unread
- **AND THEN** the second run exits 0 and writes nothing

#### Scenario: Nothing new writes nothing
- **WHEN** no condition holds and no mapped issue changed
- **THEN** `keel patrol` exits 0, the chat store's logs are unchanged, and the digest lists the roles

#### Scenario: An issue condition needs the caller's issue data
- **WHEN** a role waits for issue 42 to close and patrol runs without `--issues`, then with `--issues` listing 42 as `CLOSED`
- **THEN** the first run reports the condition unchecked and exits 0, and the second marks it met and exits 2

### Requirement: Issue labels route issue updates to roles

`keel/config.yaml` MAY declare `issue_roles:`, one `<label>: <role>` per line. When `keel patrol` receives `--issues` (the JSON `gh issue list --json number,title,state,labels,updatedAt` prints), it MUST send each role mapped from a label an issue carries one direct message for that issue's `updatedAt`, recorded with ref `issue:#<n>@<updatedAt>`, and MUST NOT send it again while that ref exists in the direct group. A line it cannot read MUST be reported and route nothing.

#### Scenario: A labelled issue reaches its role once per update
- **WHEN** `issue_roles:` maps `role:verify` to `verify` and `--issues` lists issue 157 with that label
- **THEN** patrol sends `verify` one direct message naming #157 and exits 2; a second run with the same `updatedAt` exits 0; a run with a later `updatedAt` sends one more
