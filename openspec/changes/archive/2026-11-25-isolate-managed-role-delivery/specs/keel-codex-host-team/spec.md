## ADDED Requirements

### Requirement: Managed mailbox delivery is independent across roles

Both `keel tick` and `keel codex drain` SHALL allow an independent ready managed role to receive its addressed record while another role's delivery is awaiting an endpoint. Within each role, delivery SHALL stay serial and retain its existing claims, lock and refusal semantics. The command SHALL report delivery results by role in the existing order.

#### Scenario: One endpoint has an uncertain result
- **WHEN** two independently owned roles have addressed records and one endpoint withholds an acknowledgement
- **THEN** the healthy role receives its record before that acknowledgement returns
- **AND THEN** an uncertain result retains its claim and starts no later record for the affected role
