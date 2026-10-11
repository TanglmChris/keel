## ADDED Requirements

### Requirement: A structural digest summarizes what changed since a time

`keel chat summary --since <time> [--group <g>] [--json]` MUST, for each group the caller can read, or the one `--group` names, list per sender what the sender posted since that time: the number of messages, each todo opened with its assignee and whether it is still open, each todo closed, and each record that superseded another with what it superseded, never listing a superseded record on its own. It MUST then list each record posted since that time that still waits on an acknowledgement, with the roles that have not given it. It MUST be built from the records alone, without a model or the network, and MUST NOT move any read cursor. It MUST refuse a missing or unreadable `--since` and a worktree with no role, naming the fix. With nothing since the time it MUST say so and exit 0.

#### Scenario: A coordinator's digest
- **WHEN** since the time, `rtl` posted two messages, one superseding an earlier rule, and a todo for `verify` that `verify` closed, and `verify` posted one message and a todo for `rtl` still open, and `rtl` posted a record with `--ack` that `verify` has not acknowledged
- **THEN** `keel chat summary --since <time> --json` lists under the group `rtl` with its message count, the closed todo, and the superseding record naming what it superseded, and `verify` with its message and the open todo; the superseded rule is not listed on its own; the waiting acknowledgement names `verify`
- **AND THEN** every read cursor is unchanged

#### Scenario: Nothing since the time
- **WHEN** `keel chat summary --since` names a time after the last record
- **THEN** it says nothing changed and exits 0

#### Scenario: A summary without a time or a role is refused
- **WHEN** `keel chat summary` runs without `--since`, with `--since yesterdayish`, or in a worktree with no role
- **THEN** each exits non-zero naming the fix
