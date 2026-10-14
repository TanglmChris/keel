## MODIFIED Requirements

### Requirement: Presence is visible and only an owner-installed waker launches a member

Every chat hook event and `keel chat` command MUST write the member's `presence/<role>.json` with its last activity; the SessionEnd hook MUST mark it offline. When the writer runs on the Claude desktop app, presence MUST also record its session id and Claude process id, and MUST clear them when it does not; the SessionEnd write MUST keep them. Views MUST show each member as online, idle with age, or offline with age. Posting a mention of an offline member MUST store the record and report the member as offline in the poster's output. When a post, direct message, or todo wakes a role whose recorded desktop process is not running, the output MUST say the record alone wakes nothing there (#331) and MUST name `get_session`, `unarchive_session`, `send_message`, and that role's session id as the step that does. Keel MUST NOT start any session except through a waker the owner installed for that role on that machine with `keel chat wake add`.

#### Scenario: A mention of an offline member is queued
- **WHEN** `verify`'s SessionEnd hook has run and `rtl` posts `@verify ping`
- **THEN** the record is stored and the post output names `verify` as offline

#### Scenario: A todo for an idle desktop session names its wake step
- **WHEN** `verify`'s hooks ran on the desktop app as session `local_test-331` whose process has since exited, and `rtl` runs `keel chat todo` assigning `verify`
- **THEN** the todo is stored, and the output names `send_message`, `get_session`, `unarchive_session`, and `local_test-331`; after `verify`'s hooks run again outside the desktop app, the same todo output names none of them
