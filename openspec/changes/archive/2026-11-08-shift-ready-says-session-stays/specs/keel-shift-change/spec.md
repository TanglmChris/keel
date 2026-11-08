## ADDED Requirements

### Requirement: `keel shift ready` says whether the old session will stay listed

`keel shift ready --wake` MUST NOT say, in its hint or the `clear` field of `--json`, that the old CLI session is removed when the hand-over will leave it listed. It MUST apply the hand-over's own test: the host-recorded worktree exists and is the new shift's or a role's, so `claude rm` would delete it. When that holds the hint says the session stays in `claude agents` and names the worktree and `claude attach`; otherwise it still promises removal.

#### Scenario: A session whose worktree is the new shift's is told it will stay
- **WHEN** the host recorded the worktree the session runs in as the worktree it hands over, `keep_old_sessions` is not declared, and the session runs `keel shift ready --wake`
- **THEN** the hint and the `--json` `clear` field say the session stays in `claude agents`, name that worktree, say `claude rm` would delete it and name `claude attach` with the session's id, and do not say it is removed
- **AND THEN** the hand-over that follows does not call `claude rm` for that session

#### Scenario: A removable session is still told it will be removed
- **WHEN** the host recorded no worktree for the session and nothing keeps it, and the session runs `keel shift ready --wake`
- **THEN** the hint says it is removed from the session list once Keel's store holds its transcript, and the hand-over that follows calls `claude rm` for it

#### Scenario: A kept session in use also names the shared worktree
- **WHEN** `shift: keep_old_sessions: 1` is declared, the host recorded the session's worktree as the one it hands over, and the session runs `keel shift ready --wake`
- **THEN** the hint says its conversation is kept and `claude attach` reopens it, and names that the worktree is the new shift's
