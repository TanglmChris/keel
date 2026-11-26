## ADDED Requirements

### Requirement: Read-only managed role inventory
Keel SHALL list local managed registrations for a Git repository with their recorded execution identity, effective park status and per-registration anomalies without contacting native endpoints or changing project state.

#### Scenario: Mixed local registrations
- **WHEN** the operator lists a repository containing active and parked registrations, damaged registrations and group-only roles
- **THEN** the listing includes the registrations in role order, distinguishes anomalies and parked roles, omits group-only roles, and preserves pending work and all receipts.
