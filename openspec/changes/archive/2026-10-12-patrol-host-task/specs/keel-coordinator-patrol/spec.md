## ADDED Requirements

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
