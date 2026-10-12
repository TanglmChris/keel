## ADDED Requirements

### Requirement: The patrol nudges idle roles directly

`keel patrol --nudge` MUST consider every bound role other than the patrolling role, and MUST send an idle role one direct message from `keel-patrol` when addressed records, excluding Keel's own senders, have waited longer than `--idle` (at most once per two hours), when a host-supplied `--context <role>=<percent>` is at or above `--shift-at` with nothing waiting (at most once per six hours, naming `keel shift ready --wake`), or when a note filed with `keel shift ready --wake` has waited longer than `--idle` with no wake since (once per note). A note filed without `--wake` MUST NOT be nudged to resume.

#### Scenario: Roles are nudged once each, and parked notes are left alone
- **WHEN** `verify` has an addressed message waiting, `lint` reports 62 % context, and the coordinator runs `keel patrol --nudge` twice, then `lint` files a note with `ready --wake` that no wake reaches and `verify` files one without it
- **THEN** the first run nudges `verify` for unread and `lint` for its shift, the second nudges nobody, a later run nudges `lint` to resume and not `verify`, and no run nudges `lint` over the patrol's own message
