## ADDED Requirements

### Requirement: Write-guard containment is decided on resolved paths

The write guard MUST decide whether a target is inside the guarded repository by comparing paths with symbolic links resolved on both sides, so one file gets one answer however its path is spelled. For a target that does not exist yet, Keel MUST resolve the nearest existing ancestor and compare the remainder; when no ancestor resolves, it MUST fall back to the unresolved comparison.

#### Scenario: A symlinked path does not escape the guard
- **WHEN** a guarded task's manifest is active and a write targets a file outside Touch through a symbolic link to the repository
- **THEN** the guard denies it, exactly as it denies the same file named by its resolved path
- **AND THEN** a write inside Touch is still allowed through either spelling

#### Scenario: A file that does not exist yet is still placed
- **WHEN** a guarded write targets a path that has not been created
- **THEN** containment is decided from the nearest existing ancestor
- **AND THEN** a new file inside Touch is allowed and a new file outside Touch is denied

## REMOVED Requirements

### Requirement: Repository containment is decided on resolved paths
**Reason**: #414 — the helper baseline it also governed is removed with `keel project helper`.
**Migration**: Replaced by "Write-guard containment is decided on resolved paths", which keeps the guard's rule and both of its scenarios.
