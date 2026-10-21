## ADDED Requirements

### Requirement: The bootstrap states what memory may hold and when it is rechecked
The installed bootstrap block MUST tell the session three things about memory:
- write to memory only what the next session would get wrong without it and the repository cannot answer, and never a one-off slip;
- keep one fact per entry;
- recheck memory after a fix, at a release, and at a shift change.

The block MUST stay within its documented byte budget, and Keel MUST NOT read or write the host's memory.

#### Scenario: A fresh install carries the memory rule
- **WHEN** `keel --install` runs in an empty repository
- **THEN** its `AGENTS.md` managed block says memory holds only what the repository cannot answer, and names a recheck at a shift change, within the bootstrap byte budget
