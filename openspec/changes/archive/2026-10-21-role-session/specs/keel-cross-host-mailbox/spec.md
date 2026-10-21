## ADDED Requirements

### Requirement: A role records its own session and wakes only one that still exists
A chat hook MUST resolve the session's worktree from its transcript's project directory when that names another worktree of the repository than the hook's `cwd`. A `keel chat` command MUST NOT record the calling session as the role's session unless that session started as the role, while `keel chat role --set` in a Claude Code session MUST record it. Waking MUST NOT resume a recorded session `claude agents` no longer lists.

#### Scenario: A resumed session is recorded for the worktree it runs in
- **WHEN** a CLI session's SessionStart hook reports `cwd` as rtl's worktree while its transcript lies in the project directory of verify's worktree
- **THEN** the session is recorded as verify's, with verify's worktree, and watches verify's signals
- **AND THEN** rtl's presence and session list are unchanged

#### Scenario: A visiting session does not become the role's session
- **WHEN** rtl's CLI session, recorded as rtl's, runs `keel chat unread` in verify's worktree
- **THEN** verify's recorded CLI session, worktree, and session list are unchanged

#### Scenario: Binding a role records the session that bound it
- **WHEN** a CLI session that started in a worktree with no role runs `keel chat role --set verify` there
- **THEN** verify's presence names that session and worktree, its session record names verify, and its transcript starts verify's current segment

#### Scenario: A removed session is not resumed
- **WHEN** verify's recorded CLI session has exited and `claude agents --json --all` no longer lists it
- **THEN** `keel chat wake now verify` resumes nothing and says the session was removed and that a new session must be started in verify's worktree
