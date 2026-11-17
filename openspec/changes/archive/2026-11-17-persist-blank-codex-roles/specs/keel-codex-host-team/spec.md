## ADDED Requirements

### Requirement: Successful blank role initialization supports delayed first delivery
Keel MUST preserve the exact owned thread identity across creation connection closure and delayed first use. If durable initialization cannot be verified, it MUST report that boundary and retain registration evidence rather than silently replace the thread or claim delivery succeeded.

#### Scenario: First delivery is delayed
- **WHEN** a managed role starts successfully and the creation connection closes before its first addressed record arrives
- **THEN** the same registered identity remains usable for its first work turn after normal host unloading
- **AND THEN** no substitute thread or implicit model warm-up is used
