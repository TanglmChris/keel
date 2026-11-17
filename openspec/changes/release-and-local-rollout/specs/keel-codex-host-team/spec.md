## ADDED Requirements

### Requirement: Release rollout verifies the installed host before notification

A managed-team rollout MUST verify the published package and release, installed Keel CLI/plugin versions and an actual completed model turn through the intended default host endpoint before notifying downstream repositories. It MUST preserve current native hook trust boundaries and MUST NOT interrupt unrelated active service work.

#### Scenario: Rollout is complete
- **WHEN** publication, installed version checks and the real default-host turn pass
- **THEN** the downstream owner receives one versioned update notification with verification evidence and remaining native trust limits

#### Scenario: Connectivity still fails
- **WHEN** the default host accepts RPCs but model work does not complete
- **THEN** rollout remains incomplete and no downstream completion notice is sent
