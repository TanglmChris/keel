## ADDED Requirements

### Requirement: A sender can post without waking

`keel chat post` and `keel chat dm` MUST accept `--no-wake`. A record so posted MUST be delivered and counted unread as any other, MUST carry `no_wake: yes`, and MUST NOT append to `signal/<role>` or `signal/worktree/<id>`, nor be reported by `keel chat notice --check`, nor lead `keel tick` to resume an ended session. `--no-wake` with `--ack` MUST be refused. Without the option nothing changes.

#### Scenario: A quiet post is read at the next prompt and wakes nobody
- **WHEN** `rtl` posts `@verify` with `--no-wake` in a group both belong to, and `verify` has no earlier unread
- **THEN** `signal/verify` does not exist, `keel chat unread` for `verify` lists the record, `keel chat notice --check` for `verify` exits 1, and the record file holds `no_wake: yes`

#### Scenario: A quiet direct message wakes nobody
- **WHEN** `rtl` runs `keel chat dm verify --no-wake` with a text
- **THEN** the direct group's record is unread for `verify`, `signal/verify` is not touched, and `keel chat notice --check` for `verify` exits 1

#### Scenario: The same post without the option still wakes
- **WHEN** `rtl` posts `@verify` without `--no-wake`
- **THEN** `signal/verify` ends with that record's id and `keel chat notice --check` for `verify` exits 0

#### Scenario: Asking for an acknowledgement and not waking is refused
- **WHEN** `rtl` posts `@verify` with `--ack --no-wake`
- **THEN** it exits non-zero naming both options and writes no record
