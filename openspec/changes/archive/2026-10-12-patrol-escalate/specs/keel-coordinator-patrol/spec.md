## MODIFIED Requirements

### Requirement: A patrol run reports only what changed since the last one

`keel patrol --since-last` MUST keep a snapshot per patrolling role of the shift status, the remote default branch tip, the primary worktree's uncommitted path count, each role's idleness and open todos, and the role's waking unread records older than `--idle`, and MUST report only the entries that differ from the previous run's snapshot. A first run MUST record a baseline and report no change. It MUST exit 2 when it reported a change or wrote anything, and 0 otherwise. With `--notify`, a run MUST send the patrolling role one direct message from `keel-patrol` listing only its risks — the primary checkout gaining uncommitted paths after a clean run, a host-reported `--disk-free-gb` dropping below `--disk-min-gb`, and a role that has left two unread nudges in a row unanswered — and MUST send nothing when there is none, however much changed; `--notify` without `--since-last` MUST be refused. Every run MUST append one line to the patrolling role's run log.

#### Scenario: Only a change is reported, once
- **WHEN** the coordinator runs `keel patrol --since-last --notify` three times, with `verify` running `keel shift ready` and a new commit reaching the remote between the first and second runs
- **THEN** the first run reports a baseline and exits 0, the second reports the shift status line and the remote tip as changed and exits 2 with no message, since neither is a risk, and the third reports nothing and exits 0

#### Scenario: Only risks reach the coordinator, and every run is logged
- **WHEN** the primary checkout gains an uncommitted file, the host reports 12 GB free, and `verify` leaves two unread nudges unanswered
- **THEN** each of the three is sent to the coordinator once in a message from `keel-patrol`, and the role's run log holds one line per run
