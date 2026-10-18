## MODIFIED Requirements

### Requirement: Patrol notifies the roles whose conditions are met and writes nothing otherwise

`keel patrol [--issues <file>] [--idle <duration>] [--json]` MUST run as the caller's bound role and MUST NOT fetch, schedule, or call a model. For each open wait in the groups that role can read, it MUST check the condition — a commit contained in a `refs/remotes/<remote>/` ref; an issue that `--issues` lists as closed — and for each that holds MUST write a `met` record targeting the wait and send the waiting role a direct message naming the condition and the wait, unless the waiter is the patrolling role. Without `--issues`, issue conditions MUST be reported unchecked. Patrol MUST list each bound role's presence, last activity, and open todo count, marking a role idle beyond `--idle`. It MUST exit 0 when it wrote nothing, 2 when the patrolling role has something to act on — a risk, or a wait of its own now met — 3 when it wrote records only for other roles, and 1 on an error; idleness MUST NOT change the exit status.

#### Scenario: A landed commit wakes the waiting role once
- **WHEN** `verify` waits for a commit, the commit reaches `origin`, and `rtl` runs `keel patrol` twice
- **THEN** the first run exits 3, marks the wait met, and `verify` has a direct message from `rtl` naming the commit unread
- **AND THEN** the second run exits 0 and writes nothing

#### Scenario: Nothing new writes nothing
- **WHEN** no condition holds and no mapped issue changed
- **THEN** `keel patrol` exits 0, the chat store's logs are unchanged, and the digest lists the roles

#### Scenario: An issue condition needs the caller's issue data
- **WHEN** a role waits for issue 42 to close and patrol runs without `--issues`, then with `--issues` listing 42 as `CLOSED`
- **THEN** the first run reports the condition unchecked and exits 0, and the second marks it met and exits 3

#### Scenario: Only what the coordinator must handle exits 2
- **WHEN** the coordinator runs `keel patrol --since-last --notify` after only the remote tip moved, again after its primary checkout gains an uncommitted file, then `keel patrol` after another role's wait is met, and after its own wait is met
- **THEN** the runs exit 3, 2, 3 and 2, and `keel patrol --help` names exit 3

### Requirement: Issue labels route issue updates to roles

`keel/config.yaml` MAY declare `issue_roles:`, one `<label>: <role>` per line. When `keel patrol` receives `--issues` (the JSON `gh issue list --json number,title,state,labels,updatedAt` prints), it MUST send each role mapped from a label an issue carries one direct message for that issue's `updatedAt`, recorded with ref `issue:#<n>@<updatedAt>`, and MUST NOT send it again while that ref exists in the direct group. A line it cannot read MUST be reported and route nothing.

#### Scenario: A labelled issue reaches its role once per update
- **WHEN** `issue_roles:` maps `role:verify` to `verify` and `--issues` lists issue 157 with that label
- **THEN** patrol sends `verify` one direct message naming #157 and exits 3; a second run with the same `updatedAt` exits 0; a run with a later `updatedAt` sends one more

### Requirement: A patrol run reports only what changed since the last one

`keel patrol --since-last` MUST keep a snapshot per patrolling role of the shift status, the remote default branch tip, the primary worktree's uncommitted path count, each role's idleness and open todos, and the role's waking unread records older than `--idle`, and MUST report only the entries that differ from the previous run's snapshot. A first run MUST record a baseline and report no change. It MUST exit 2 when it found a risk, 3 when it reported a change or wrote anything with no risk, and 0 otherwise. With `--notify`, a run MUST send the patrolling role one direct message from `keel-patrol` listing only its risks — the primary checkout gaining uncommitted paths after a clean run, a host-reported `--disk-free-gb` dropping below `--disk-min-gb`, and a role that has left two unread nudges in a row unanswered — and MUST send nothing when there is none, however much changed; `--notify` without `--since-last` MUST be refused. Every run MUST append one line to the patrolling role's run log.

#### Scenario: Only a change is reported, once
- **WHEN** the coordinator runs `keel patrol --since-last --notify` three times, with `verify` running `keel shift ready` and a new commit reaching the remote between the first and second runs
- **THEN** the first run reports a baseline and exits 0, the second reports the shift status line and the remote tip as changed and exits 3 with no message, since neither is a risk, and the third reports nothing and exits 0

#### Scenario: Only risks reach the coordinator, and every run is logged
- **WHEN** the primary checkout gains an uncommitted file, the host reports 12 GB free, and `verify` leaves two unread nudges unanswered
- **THEN** each of the three is sent to the coordinator once in a message from `keel-patrol`, and the role's run log holds one line per run
