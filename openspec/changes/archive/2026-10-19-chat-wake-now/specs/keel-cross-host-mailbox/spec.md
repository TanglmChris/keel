## MODIFIED Requirements

### Requirement: Presence is visible and only an owner-installed waker launches a member

Every chat hook event and `keel chat` command MUST write the member's `presence/<role>.json` with its last activity; the SessionEnd hook MUST mark it offline. When the writer runs on the Claude desktop app, presence MUST also record its session id and Claude process id, and MUST clear them when it does not; the SessionEnd write MUST keep them. Views MUST show each member as online, idle with age, or offline with age. Posting a mention of an offline member MUST store the record and report the member as offline in the poster's output. When a post, direct message, or todo wakes a role whose recorded desktop process is not running, the output MUST say the record alone wakes nothing there (#331) and MUST name `get_session`, `unarchive_session`, `send_message`, and that role's session id as the step that does. When the writer runs in a Claude Code CLI session, presence MUST also record its session id, Claude process id and worktree. When a post, direct message, or todo wakes a role whose recorded CLI process is not running, the output MUST name `keel chat wake now <role>`; that command MUST then resume the role's recorded session with `claude --bg --resume <session> "<prompt>"` and no other flag, in the recorded worktree, and MUST run nothing while the process is running. `keel tick` MUST do the same at most once per new addressed record for each role that is not parked. Keel MUST NOT start any session except through a waker the owner installed for that role on that machine with `keel chat wake add`, through `keel tick` run by the job the owner installed from `keel tick task`, or through `keel chat wake now`, and the last two MUST only resume a session the role recorded.

#### Scenario: A mention of an offline member is queued
- **WHEN** `verify`'s SessionEnd hook has run and `rtl` posts `@verify ping`
- **THEN** the record is stored and the post output names `verify` as offline

#### Scenario: A todo for an idle desktop session names its wake step
- **WHEN** `verify`'s hooks ran on the desktop app as session `local_test-331` whose process has since exited, and `rtl` runs `keel chat todo` assigning `verify`
- **THEN** the todo is stored, and the output names `send_message`, `get_session`, `unarchive_session`, and `local_test-331`; after `verify`'s hooks run again outside the desktop app, the same todo output names none of them

#### Scenario: An ended CLI session is resumed in one step
- **WHEN** `verify`'s hooks ran in a CLI session `sess-verify-1` whose process has exited, and `rtl` sends it a direct message and runs `keel chat wake now verify`
- **THEN** the post names `keel chat wake now verify` and not `get_session`, and the command runs `claude --bg --resume sess-verify-1 <prompt>` with no other argument, in verify's worktree
- **AND THEN** with the process running it runs nothing and says the session is running; `keel tick` resumes the exited session once for a new record, not again for the same record, and never while the role is parked
