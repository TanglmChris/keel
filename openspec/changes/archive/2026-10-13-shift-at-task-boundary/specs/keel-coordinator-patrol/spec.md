## MODIFIED Requirements

### Requirement: The patrol nudges idle roles directly

`keel patrol --nudge` MUST consider every bound role other than the patrolling role, and MUST send an idle role one direct message from `keel-patrol` when addressed records, excluding Keel's own senders, have waited longer than `--idle` (at most once per two hours), when a todo assigned to it has been closed since the patrol last looked (once per closure, naming `keel shift ready --wake` when another todo is still open for it and plain `keel shift ready` otherwise; the first run only records existing closures), or when a note filed with `keel shift ready --wake` has waited longer than `--idle` with no wake since (once per note). A note filed without `--wake` MUST NOT be nudged to resume. `--context` and `--shift-at` MUST be refused, naming their retirement: context never triggers a shift.

#### Scenario: Roles are nudged once each, and parked notes are left alone
- **WHEN** `verify` has an addressed message waiting, `lint` holds two todos it has read, and the coordinator runs `keel patrol --nudge`, `lint` closes one todo, the coordinator runs it twice more, `lint` closes the other and it runs again, then `lint` files a note with `ready --wake` that no wake reaches and `verify` files one without it
- **THEN** the first run nudges `verify` for unread and not `lint`, the second nudges `lint` to change shift naming `ready --wake`, the third nudges nobody, the fourth nudges `lint` naming plain `ready` and the coordinator, a later run nudges `lint` to resume and not `verify`, no run nudges `lint` over the patrol's own message, and `--context` is refused
