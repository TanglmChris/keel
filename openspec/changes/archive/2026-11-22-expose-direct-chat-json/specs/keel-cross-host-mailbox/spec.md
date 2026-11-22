## ADDED Requirements

### Requirement: Direct chat reads include canonical participants

Keel MUST expose the canonical participants of a direct chat record in its public JSON `direct` field, regardless of whether the repository has any role renames. JSON reads MUST preserve existing records and read cursors. Ordinary group records MUST NOT acquire direct participants. Direct records marked `no_wake` MUST still expose participants while remaining ineligible to wake a role.

#### Scenario: A public reader reads one DM through different surfaces
- **WHEN** unread, group peek, or show reads an ordinary direct message with or without a role rename
- **THEN** these surfaces report the same record ID and canonical direct participants without writing stored records or read cursors

#### Scenario: A no-wake DM and an ordinary group message retain wake behavior
- **WHEN** a no-wake DM and an unaddressed ordinary group message are read as JSON
- **THEN** only the DM includes direct participants and neither record wakes its recipient
