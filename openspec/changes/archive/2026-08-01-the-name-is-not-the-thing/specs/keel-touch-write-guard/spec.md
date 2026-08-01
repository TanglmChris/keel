## ADDED Requirements

### Requirement: Repository containment is decided on resolved paths

The write guard MUST decide whether a target is inside the guarded repository by comparing paths with symbolic links resolved on both sides. One file MUST get one answer however its path is spelled, so a target reached through a symbolic link MUST NOT escape the guard that denies the same file reached directly.

When the target does not yet exist, Keel MUST resolve the nearest existing ancestor and compare the remainder against it, because a guarded write is usually a file that is about to be created. When no ancestor resolves, Keel MUST fall back to the unresolved comparison rather than failing open or closed on an unreadable directory.

The helper baseline check MUST answer the same question the same way, so a baseline path inside the worktree is refused whether or not the worktree is reached through a link.

#### Scenario: A symlinked path does not escape the guard
- **WHEN** a guarded task's manifest is active and a write targets a file outside Touch through a symbolic link to the repository
- **THEN** the guard denies it, exactly as it denies the same file named by its resolved path
- **AND THEN** a write inside Touch is still allowed through either spelling

#### Scenario: A file that does not exist yet is still placed
- **WHEN** a guarded write targets a path that has not been created
- **THEN** containment is decided from the nearest existing ancestor
- **AND THEN** a new file inside Touch is allowed and a new file outside Touch is denied

#### Scenario: A helper baseline inside a linked worktree is refused
- **WHEN** a helper baseline path resolves inside the repository worktree, reached through a symbolic link
- **THEN** the capture is refused
- **AND THEN** a baseline that genuinely resolves outside the worktree is still accepted
