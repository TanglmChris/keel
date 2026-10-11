## ADDED Requirements

### Requirement: A record can ask for an acknowledgement, and who has given it is listed

`keel chat post … --ack` and `keel chat todo … --ack` MUST mark the record as asking for an acknowledgement from the roles it addresses: the group's other members it would wake, and every other member when it mentions `@all`; a record that addresses nobody MUST be refused with `--ack`. `keel chat ack <id>` MUST record an acknowledgement, mark the record read for that role, and wake nobody; it MUST be refused, naming why, for a record that does not ask, for a role the record does not address, and for a role that already acknowledged it. A reply to the record from an addressed role MUST count as its acknowledgement. For a record that asks, `keel chat show <id>` MUST list which addressed roles acknowledged, which read it without acknowledging, and which have not read it, and `keel chat acks [--mine]` MUST list every record that asks and still waits on an addressed role, with the same lists, `--mine` keeping those the caller posted. A group view and the wake notice MUST mark a record that asks with `(ack requested)`. The Slack bridge MUST NOT post an acknowledgement.

#### Scenario: A sender sees who has not acknowledged
- **WHEN** `rtl` posts `@verify @spec rerun R007 on 1b64e8c` with `--ack`, `verify` runs `keel chat ack <id>`, and `spec` reads the group without acknowledging
- **THEN** `keel chat show <id>` lists `verify` as acknowledged and `spec` as read but not acknowledged, and `keel chat acks --mine` for `rtl` lists the record waiting on `spec`

#### Scenario: A reply acknowledges
- **WHEN** `spec` replies to that record
- **THEN** `keel chat show <id>` lists `spec` as acknowledged and `keel chat acks` no longer lists the record

#### Scenario: Acknowledging is refused where it means nothing
- **WHEN** a role acknowledges a record that does not ask, a record that does not address it, or a record it already acknowledged, or a record that addresses nobody is posted with `--ack`
- **THEN** each is refused naming why

#### Scenario: An acknowledgement wakes nobody and is marked where it is asked
- **WHEN** `verify` acknowledges, and `spec` views the group before acknowledging
- **THEN** `rtl` has nothing new unread from the acknowledgement, and `spec`'s view and wake notice show the record with `(ack requested)`
