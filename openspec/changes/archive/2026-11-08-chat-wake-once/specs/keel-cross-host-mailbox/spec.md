## ADDED Requirements

### Requirement: A record wakes a session once and the wake lists what is new

For a hook payload carrying a session id, the FileChanged hook MUST announce a waking record to that session at most once, however many signal files changed for it, and MUST exit 0 with no output when no waking record is new to the session. Its notice MUST list the waking records not yet announced and state how many records are unread in all. SessionStart and UserPromptSubmit MUST count the records their notices list as announced, and SessionStart MUST first forget what was announced to that session id. A payload without a session id MUST behave as before. `keel chat notice` and `keel chat check` MUST NOT record anything as announced.

#### Scenario: One message, two signal files, one wake
- **WHEN** `rtl` posts `@verify please rerun` and the FileChanged hook runs twice for session `s1` of `verify`, as the role signal and the worktree signal both changed
- **THEN** the first run exits 2 and names the record, and the second exits 0 with no output

#### Scenario: A later message wakes again and lists only itself
- **WHEN** a second mention arrives after the first was announced to `s1`, and FileChanged runs
- **THEN** it exits 2, names only the second record, and states the total unread

#### Scenario: What SessionStart showed is not repeated
- **WHEN** a mention is unread, SessionStart for `s1` lists it, and FileChanged runs for `s1`
- **THEN** FileChanged exits 0; and after SessionStart runs again for `s1` (a resume), FileChanged exits 2 for that record

#### Scenario: Two hooks at once announce once
- **WHEN** two FileChanged hooks for the same session and record start together
- **THEN** exactly one exits 2

#### Scenario: Another session is told separately
- **WHEN** session `s2` of the same role runs FileChanged for a record already announced to `s1`
- **THEN** it exits 2
