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

### Requirement: The patrolling role is reminded to re-arm its schedule

`keel/config.yaml` MAY declare `patrol:` with `role:` naming a chat role and `every:` a duration of the form `<n>s`, `<n>m`, `<n>h`, or `<n>d`. In a worktree bound to that role, `keel context` MUST carry `patrol` with the role and interval, the SessionStart and compaction projection MUST state that the role runs `keel patrol` at that interval and that a session's schedule ends with the session, and `keel shift resume` MUST end with the same reminder. Keel MUST NOT create the schedule. A declaration missing either value, or with a malformed one, MUST be reported and MUST remind nobody; a worktree bound to another role MUST get no reminder.

#### Scenario: A new shift of the coordinator is reminded
- **WHEN** `patrol:` declares `role: iecc-pm` and `every: 30m`, and a worktree bound to `iecc-pm` starts a session and runs `keel shift resume`
- **THEN** `keel context --json` carries `patrol` with `iecc-pm` and `30m`, the projection names `keel patrol` and `30m`, and the resume output ends with the reminder

#### Scenario: Other roles and broken declarations are quiet
- **WHEN** the worktree is bound to `rtl`, or `every:` reads `soon`
- **THEN** no `patrol` field or reminder appears, and the malformed declaration is reported in warnings

### Requirement: A patrol run reports only what changed since the last one

`keel patrol --since-last` MUST keep a snapshot per patrolling role of the shift status, the remote default branch tip, the primary worktree's uncommitted path count, each role's idleness and open todos, and the role's waking unread records older than `--idle`, and MUST report only the entries that differ from the previous run's snapshot. A first run MUST record a baseline and report no change. It MUST exit 2 when it reported a change or wrote anything, and 0 otherwise. With `--notify`, a run that reported changes MUST send them to the patrolling role as one direct message from `keel-patrol`, and a run with no change MUST send nothing; `--notify` without `--since-last` MUST be refused.

#### Scenario: Only a change is reported, once
- **WHEN** the coordinator runs `keel patrol --since-last --notify` three times, with `verify` running `keel shift ready` and a new commit reaching the remote between the first and second runs
- **THEN** the first run reports a baseline and exits 0, the second reports the shift status line and the remote tip as changed and exits 2 with one message from `keel-patrol` waking the coordinator, and the third reports nothing and exits 0 with no further message

### Requirement: The patrol's host task is declared and rendered, never installed by Keel

`patrol:` MAY declare `host_task:` and `model:`; Keel MUST NOT choose a model. With `host_task:` declared, the patrolling role's reminder MUST name the host task and ask to confirm it is still enabled instead of to re-create a session schedule. `keel patrol task` MUST print a self-contained host task — its id, a cron suggested from `every:`, the declared model or a statement that none is declared, and a prompt that runs `keel patrol --since-last --notify` against the role's worktree by path — and MUST create nothing; it MUST be refused without a valid `patrol:` or without a worktree bound to its role.

#### Scenario: The host task is rendered from the declaration
- **WHEN** `patrol:` declares `role: rtl`, `every: 30m`, and `host_task: soc-patrol`, and `keel patrol task` runs
- **THEN** it prints task id `soc-patrol`, cron `*/30 * * * *`, that no model is declared, and a prompt containing `keel patrol --repo <rtl's worktree> --since-last --notify`, and no file under the repository changes

#### Scenario: A declared host task changes the reminder
- **WHEN** `patrol:` declares `host_task: soc-patrol` and a session starts in the worktree bound to its role
- **THEN** `keel context` carries `patrol.hostTask` `soc-patrol` and the session-start note says the host task outlives the session and asks to confirm it is enabled
